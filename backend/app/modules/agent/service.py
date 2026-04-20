from __future__ import annotations

import json
import logging
import re
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.core.config import settings
from app.integrations.gemini_client import generate_json_response
from app.models.message import MessageModel
from app.models.ticket import TicketModel
from app.modules.agent.schemas import (
    AgentDecision,
    AgentProcessIn,
    AgentProcessOut,
    OpenTicketContext,
    RecentMessageContext,
)
from app.modules.messages.service import list_recent_messages_by_phone
from app.modules.tickets.service import close_ticket, create_ticket, list_open_tickets_for_phone, update_open_ticket_summary

logger = logging.getLogger(__name__)

AREAS = ("soporte_tecnico", "pagos", "envios", "reclamos", "ventas", "otros")
RECENT_MESSAGES_LIMIT = 20
MAX_OPEN_TICKETS = 5
WAITING_MESSAGE_GENERIC = "Gracias por escribirnos. Estamos revisando tu caso y te respondemos enseguida."

BASE_PROMPT = """Eres un agente de triage para WhatsApp de Customer Success de Pueblo Lindo. Tu nombre es Pueblo Agent.
Decide UNA accion para el mensaje entrante:
- create_ticket: crear un ticket nuevo
- update_ticket: actualizar resumen/area de un ticket abierto existente
- no_action: no crear ni actualizar ticket

Reglas obligatorias:
- Solo puedes actualizar tickets abiertos.
- Si hay multiples tickets abiertos, elige el ticket que tenga mayor relacion semantica con el mensaje.
- Si no hay relacion clara y el mensaje expresa una incidencia o solicitud nueva, crea ticket nuevo.
- Usa solo estas areas: soporte_tecnico, pagos, envios, reclamos, ventas, otros.
- El summary debe ser breve, accionable y en espanol.

Responde SOLAMENTE con JSON valido con esta forma:
{
  "action": "create_ticket" | "update_ticket" | "no_action",
  "create_ticket": {"area": string, "summary": string} | null,
  "update_ticket": {"ticket_id": string, "area": string, "summary": string, "reason": string} | null,
  "no_action": {"reason": string} | null
}
"""


def build_waiting_message() -> str:
    return WAITING_MESSAGE_GENERIC


def _ticket_context(ticket: TicketModel) -> OpenTicketContext:
    return OpenTicketContext(
        id=ticket.id,
        area=ticket.area,
        summary=ticket.summary,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        last_activity_at=ticket.last_activity_at,
    )


def _message_context(message: MessageModel) -> RecentMessageContext:
    sender = "user" if message.sender == "user" else "agent"
    return RecentMessageContext(sender=sender, content=message.content, created_at=message.created_at)


def _fallback_decision(message: str, open_tickets: list[TicketModel]) -> AgentDecision:
    text = message.lower()
    new_ticket_hints = ("nuevo", "otro", "ademas", "tambien", "nueva consulta")
    if open_tickets and not any(hint in text for hint in new_ticket_hints):
        latest = open_tickets[0]
        return AgentDecision(
            action="update_ticket",
            update_ticket={
                "ticket_id": str(latest.id),
                "area": latest.area if latest.area in AREAS else "otros",
                "summary": f"{latest.summary} | Actualizacion: {message}".strip(" |"),
                "reason": "Sin LLM disponible, se actualiza ticket abierto mas reciente.",
            },
        )

    return AgentDecision(
        action="create_ticket",
        create_ticket={
            "area": "otros",
            "summary": f"Cliente reporta: {message}",
        },
    )


async def _decide_with_llm(
    *,
    payload: AgentProcessIn,
    open_tickets: list[TicketModel],
    recent_messages: list[MessageModel],
) -> AgentDecision:
    context = {
        "phone": payload.phone,
        "incoming_message": payload.message,
        "open_tickets": [_ticket_context(ticket).model_dump(mode="json") for ticket in open_tickets],
        "recent_messages": [_message_context(message).model_dump(mode="json") for message in recent_messages],
        "hard_limits": {
            "max_open_tickets": MAX_OPEN_TICKETS,
            "recent_messages_limit": RECENT_MESSAGES_LIMIT,
        },
    }
    prompt = f"{BASE_PROMPT}\n\nContexto:\n{json.dumps(context, ensure_ascii=True)}"

    try:
        raw = await generate_json_response(prompt=prompt, model=settings.gemini_model_primary)
    except Exception:
        raw = await generate_json_response(prompt=prompt, model=settings.gemini_model_fallback)

    try:
        return AgentDecision.model_validate_json(raw)
    except ValidationError:
        logger.warning("agent_invalid_llm_json raw=%s", raw)
        return _fallback_decision(payload.message, open_tickets)


def _merge_summaries(old_summary: str, new_summary: str) -> str:
    if not old_summary.strip():
        return new_summary
    return f"{old_summary} | {new_summary}"


def _summary_title(summary: str) -> str:
    cleaned = " ".join(summary.split())
    if not cleaned:
        return "Sin titulo"
    if len(cleaned) <= 72:
        return cleaned
    return f"{cleaned[:69]}..."


def _build_close_ticket_options_message(open_tickets: list[TicketModel]) -> str:
    lines = [
        f"Tienes el maximo de {MAX_OPEN_TICKETS} tickets abiertos.",
        "Para abrir un ticket nuevo, primero cierra uno enviando: CERRAR <numero>",
        "Tickets abiertos:",
    ]
    for idx, ticket in enumerate(open_tickets, start=1):
        lines.append(f"{idx}) {ticket.id} - {_summary_title(ticket.summary)}")
    return "\n".join(lines)


def _extract_close_choice(message: str, total_tickets: int) -> int | None:
    match = re.search(r"\b(?:cerrar|close)\s*#?\s*(\d{1,2})\b", message.lower())
    if not match:
        return None
    choice = int(match.group(1))
    if choice < 1 or choice > total_tickets:
        return None
    return choice


def _is_explicit_new_ticket_request(message: str) -> bool:
    lowered = message.lower()
    hints = (
        "nuevo ticket",
        "crear ticket nuevo",
        "abrir ticket nuevo",
        "es otro problema",
        "es un problema distinto",
    )
    return any(hint in lowered for hint in hints)


def _tokenize_for_similarity(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]{3,}", text.lower())
    stop_words = {
        "para",
        "pero",
        "este",
        "esta",
        "hola",
        "buenas",
        "gracias",
        "ticket",
        "favor",
        "quiero",
        "tengo",
        "sobre",
        "porque",
    }
    return {token for token in tokens if token not in stop_words}


def _best_matching_open_ticket(message: str, open_tickets: list[TicketModel]) -> TicketModel | None:
    message_tokens = _tokenize_for_similarity(message)
    if not message_tokens:
        return None

    best_ticket: TicketModel | None = None
    best_score = 0
    for ticket in open_tickets:
        ticket_tokens = _tokenize_for_similarity(ticket.summary)
        if not ticket_tokens:
            continue
        score = len(message_tokens & ticket_tokens)
        if score > best_score:
            best_score = score
            best_ticket = ticket

    if best_score == 0:
        return None
    return best_ticket


def _build_ticket_reply(action: str, ticket: TicketModel | None, reason: str | None = None) -> str:
    if ticket is None:
        return "Recibimos tu mensaje. Un asesor revisara tu caso pronto."

    wa_link = f"https://wa.me/{''.join(ch for ch in ticket.user_phone if ch.isdigit())}"
    if action == "create_ticket":
        return (
            f"Ticket creado: {ticket.id}. Area: {ticket.area}. "
            f"Resumen: {ticket.summary}. Contacto rapido: {wa_link}"
        )
    if action == "update_ticket":
        return (
            f"Ticket actualizado: {ticket.id}. Area: {ticket.area}. "
            f"Resumen actual: {ticket.summary}. Contacto rapido: {wa_link}"
        )
    reason_text = f" Motivo: {reason}" if reason else ""
    return f"Recibimos tu mensaje y seguimos atentos.{reason_text}"


async def run_ticket_agent(payload: AgentProcessIn) -> AgentProcessOut:
    open_tickets = list_open_tickets_for_phone(payload.phone, limit=MAX_OPEN_TICKETS)
    recent_messages = list_recent_messages_by_phone(payload.phone, limit=RECENT_MESSAGES_LIMIT)

    close_choice = _extract_close_choice(payload.message, len(open_tickets))
    if close_choice is not None and open_tickets:
        target = open_tickets[close_choice - 1]
        closed = close_ticket(target.id)
        if closed is not None:
            reply = (
                f"Cerramos el ticket {target.id}. "
                "Ahora puedes enviarnos tu nuevo problema y creamos otro ticket."
            )
        else:
            reply = "No se pudo cerrar ese ticket. Intenta nuevamente con el numero listado."
        return AgentProcessOut(
            action="no_action",
            ticket_id=target.id,
            area=target.area,
            summary=target.summary,
            wa_link=f"https://wa.me/{''.join(ch for ch in payload.phone if ch.isdigit())}",
            reply_message=reply,
        )

    decision: AgentDecision
    if settings.gemini_api_key:
        try:
            decision = await _decide_with_llm(payload=payload, open_tickets=open_tickets, recent_messages=recent_messages)
        except Exception as exc:
            logger.warning("agent_llm_failed err=%s", exc)
            decision = _fallback_decision(payload.message, open_tickets)
    else:
        decision = _fallback_decision(payload.message, open_tickets)

    if decision.action == "create_ticket" and open_tickets and not _is_explicit_new_ticket_request(payload.message):
        matched = _best_matching_open_ticket(payload.message, open_tickets)
        if matched is not None:
            merged = _merge_summaries(matched.summary, f"Actualizacion: {payload.message}")
            updated = update_open_ticket_summary(matched.id, matched.area, merged)
            if updated is not None:
                return AgentProcessOut(
                    action="update_ticket",
                    ticket_id=updated.id,
                    area=updated.area,
                    summary=updated.summary,
                    wa_link=f"https://wa.me/{''.join(ch for ch in updated.user_phone if ch.isdigit())}",
                    reply_message=_build_ticket_reply("update_ticket", updated),
                )

    if decision.action == "create_ticket" and decision.create_ticket is not None:
        # Keep a hard cap of open tickets per user.
        if len(open_tickets) >= MAX_OPEN_TICKETS:
            return AgentProcessOut(
                action="no_action",
                ticket_id=open_tickets[0].id,
                area=open_tickets[0].area,
                summary=open_tickets[0].summary,
                wa_link=f"https://wa.me/{''.join(ch for ch in payload.phone if ch.isdigit())}",
                reply_message=_build_close_ticket_options_message(open_tickets),
            )
        else:
            ticket = create_ticket(payload.phone, area=decision.create_ticket.area, summary=decision.create_ticket.summary)

        return AgentProcessOut(
            action="create_ticket",
            ticket_id=ticket.id,
            area=ticket.area,
            summary=ticket.summary,
            wa_link=f"https://wa.me/{''.join(ch for ch in ticket.user_phone if ch.isdigit())}",
            reply_message=_build_ticket_reply("create_ticket", ticket),
        )

    if decision.action == "update_ticket" and decision.update_ticket is not None:
        target_id: UUID = decision.update_ticket.ticket_id
        open_ticket_by_id = {ticket.id: ticket for ticket in open_tickets}
        target = open_ticket_by_id.get(target_id)
        if target is None and open_tickets:
            target = open_tickets[0]
            target_id = target.id

        if target is None:
            created = create_ticket(
                payload.phone,
                area=decision.update_ticket.area,
                summary=decision.update_ticket.summary,
            )
            return AgentProcessOut(
                action="create_ticket",
                ticket_id=created.id,
                area=created.area,
                summary=created.summary,
                wa_link=f"https://wa.me/{''.join(ch for ch in created.user_phone if ch.isdigit())}",
                reply_message=_build_ticket_reply("create_ticket", created),
            )

        merged = _merge_summaries(target.summary, decision.update_ticket.summary)
        updated = update_open_ticket_summary(
            target_id,
            decision.update_ticket.area,
            merged,
        )
        if updated is None:
            created = create_ticket(payload.phone, area=decision.update_ticket.area, summary=decision.update_ticket.summary)
            return AgentProcessOut(
                action="create_ticket",
                ticket_id=created.id,
                area=created.area,
                summary=created.summary,
                wa_link=f"https://wa.me/{''.join(ch for ch in created.user_phone if ch.isdigit())}",
                reply_message=_build_ticket_reply("create_ticket", created),
            )

        return AgentProcessOut(
            action="update_ticket",
            ticket_id=updated.id,
            area=updated.area,
            summary=updated.summary,
            wa_link=f"https://wa.me/{''.join(ch for ch in updated.user_phone if ch.isdigit())}",
            reply_message=_build_ticket_reply("update_ticket", updated),
        )

    no_action_reason = decision.no_action.reason if decision.no_action else "Sin motivo especificado."
    if open_tickets:
        target = open_tickets[0]
        merged = _merge_summaries(target.summary, f"Actualizacion: {payload.message}")
        updated = update_open_ticket_summary(target.id, target.area, merged)
        if updated is not None:
            return AgentProcessOut(
                action="update_ticket",
                ticket_id=updated.id,
                area=updated.area,
                summary=updated.summary,
                wa_link=f"https://wa.me/{''.join(ch for ch in updated.user_phone if ch.isdigit())}",
                reply_message=_build_ticket_reply("no_action", updated, no_action_reason),
            )

    created = create_ticket(payload.phone, area="otros", summary=f"Cliente reporta: {payload.message}")
    return AgentProcessOut(
        action="create_ticket",
        ticket_id=created.id,
        area=created.area,
        summary=created.summary,
        wa_link=f"https://wa.me/{''.join(ch for ch in created.user_phone if ch.isdigit())}",
        reply_message=_build_ticket_reply("no_action", created, no_action_reason),
    )
