from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import logging
import re
import unicodedata
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
LLM_UNAVAILABLE_MESSAGE = "Gemini no está disponible en este momento. Intentalo de nuevo más tarde"
INTAKE_SESSION_TTL_MINUTES = 30


@dataclass(slots=True)
class IntakeSession:
    area: str
    summary_seed: str
    slot_values: dict[str, str] = field(default_factory=dict)
    collected_text: str = ""
    awaiting_confirmation: bool = False
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


INTAKE_SESSIONS: dict[str, IntakeSession] = {}

AREA_INTAKE_RULES: dict[str, dict[str, Any]] = {
    "soporte_tecnico": {
        "required": ("detail", "channel", "error_context"),
        "mandatory": ("detail", "channel"),
        "threshold": 0.67,
    },
    "pagos": {
        "required": ("detail", "reference", "payment_method"),
        "mandatory": ("detail", "reference"),
        "threshold": 0.67,
    },
    "envios": {
        "required": ("detail", "reference", "shipping_context"),
        "mandatory": ("detail", "reference"),
        "threshold": 0.67,
    },
    "reclamos": {
        "required": ("detail", "reference", "impact"),
        "mandatory": ("detail",),
        "threshold": 0.67,
    },
    "ventas": {
        "required": ("detail", "reference", "user_role"),
        "mandatory": ("detail", "reference"),
        "threshold": 0.67,
    },
    "otros": {
        "required": ("detail", "reference"),
        "mandatory": ("detail",),
        "threshold": 0.5,
    },
}

INTAKE_SLOT_LABELS = {
    "detail": "Detalle del problema",
    "reference": "ID o referencia (pedido/transaccion/publicacion)",
    "payment_method": "Metodo de pago",
    "shipping_context": "Dato de envio (tracking/courier/direccion)",
    "channel": "Canal o modulo donde falla (app/web/login/checkout)",
    "error_context": "Mensaje de error o contexto tecnico",
    "impact": "Impacto del problema",
    "user_role": "Rol del usuario (comprador/artesano)",
}

BASE_PROMPT = """Eres Pueblo Agent, agente de triage de Pueblo Lindo.
Pueblo Lindo es un marketplace que conecta artesanos rurales de Latinoamerica con compradores de todo el mundo.

Tu objetivo es gestionar incidencias operativas del marketplace, no consultas generales.

Decide UNA accion para el mensaje entrante:
- create_ticket: crear ticket nuevo
- update_ticket: actualizar resumen/area de un ticket abierto existente
- no_action: no crear ni actualizar ticket

Reglas obligatorias:
- Solo puedes actualizar tickets abiertos.
- Si hay multiples tickets abiertos, elige el ticket con mayor relacion semantica.
- Si no hay relacion clara y el mensaje describe un incidente nuevo del marketplace, crea ticket nuevo.
- Si el mensaje NO es una incidencia del marketplace (ej: programacion, salud, familia, finanzas personales, tareas, curiosidades, consultas generales), usa no_action.
- Si el usuario menciona "marketplace" pero pide ayuda no operativa (ej: escribir codigo, resolver tareas, consultas personales), usa no_action.
- Solo crea/actualiza ticket si hay evidencia explicita de problema operativo del marketplace que pueda derivarse a un area.
- Usa solo estas areas y su alcance:
    - soporte_tecnico: errores de plataforma, login, cuenta, bugs, fallas tecnicas.
    - pagos: cobros, pagos rechazados, reembolsos, facturacion.
    - envios: estado de envio, demoras, no entrega, tracking.
    - reclamos: quejas formales, disconformidad, mala experiencia, disputa.
    - ventas: dudas comerciales sobre compra/venta dentro del marketplace.
    - otros: incidencias reales del marketplace que no calzan claramente en las anteriores.
- El summary debe ser breve, accionable y en espanol.

Responde SOLO con JSON valido en esta forma:
{
    "action": "create_ticket" | "update_ticket" | "no_action",
    "create_ticket": {"area": string, "summary": string} | null,
    "update_ticket": {"ticket_id": string, "area": string, "summary": string, "reason": string} | null,
    "no_action": {"reason": string} | null
}
"""


def build_waiting_message() -> str:
    return WAITING_MESSAGE_GENERIC


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _cleanup_intake_sessions() -> None:
    now = _now_utc()
    ttl = timedelta(minutes=INTAKE_SESSION_TTL_MINUTES)
    expired_phones = [
        phone
        for phone, session in INTAKE_SESSIONS.items()
        if now - session.updated_at > ttl
    ]
    for phone in expired_phones:
        INTAKE_SESSIONS.pop(phone, None)


def _get_intake_session(phone: str) -> IntakeSession | None:
    _cleanup_intake_sessions()
    return INTAKE_SESSIONS.get(phone)


def _upsert_intake_session(phone: str, session: IntakeSession) -> None:
    session.updated_at = _now_utc()
    INTAKE_SESSIONS[phone] = session


def _clear_intake_session(phone: str) -> None:
    INTAKE_SESSIONS.pop(phone, None)


def _intake_rule_for_area(area: str) -> dict[str, Any]:
    return AREA_INTAKE_RULES.get(area, AREA_INTAKE_RULES["otros"])


def _shorten(text: str, max_len: int = 180) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_len:
        return cleaned
    return f"{cleaned[: max_len - 3]}..."


def _extract_reference_slot(compact: str) -> str | None:
    patterns = (
        r"\b(?:pedido|orden|order|transaccion|pago|id|nro|numero|guia|tracking|publicacion)\s*[:#-]?\s*([a-z0-9-]{4,})\b",
        r"\b([a-z]{2,}-\d{3,})\b",
        r"\b(\d{6,})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, compact)
        if match:
            return match.group(1)
    return None


def _extract_detail_slot(original_message: str, compact: str) -> str | None:
    signals = (
        "problema",
        "error",
        "falla",
        "no puedo",
        "no funciona",
        "demora",
        "rechaz",
        "duplic",
        "bloque",
        "cancel",
        "reclamo",
    )
    if len(compact) < 20:
        return None
    if not any(signal in compact for signal in signals):
        return None
    return _shorten(original_message)


def _extract_payment_method_slot(compact: str) -> str | None:
    values = ("tarjeta", "yape", "plin", "transferencia", "paypal", "visa", "mastercard")
    for value in values:
        if value in compact:
            return value
    return None


def _extract_shipping_context_slot(compact: str) -> str | None:
    values = ("tracking", "guia", "courier", "direccion", "ciudad", "entrega")
    for value in values:
        if value in compact:
            return value
    return None


def _extract_channel_slot(compact: str) -> str | None:
    values = ("app", "web", "login", "checkout", "carrito", "cuenta")
    for value in values:
        if value in compact:
            return value
    return None


def _extract_error_context_slot(original_message: str, compact: str) -> str | None:
    if "error" in compact or "codigo" in compact:
        return _shorten(original_message)
    return None


def _extract_impact_slot(compact: str) -> str | None:
    values = ("urgente", "afecta", "perdida", "perdi", "molesto", "grave")
    for value in values:
        if value in compact:
            return value
    return None


def _extract_user_role_slot(compact: str) -> str | None:
    if "artesano" in compact or "vendedor" in compact:
        return "artesano"
    if "comprador" in compact or "cliente" in compact:
        return "comprador"
    return None


def _extract_slot_values(area: str, message: str) -> dict[str, str]:
    compact = " ".join(_normalize_text(message).split())
    values: dict[str, str] = {}

    detail = _extract_detail_slot(message, compact)
    if detail:
        values["detail"] = detail

    reference = _extract_reference_slot(compact)
    if reference:
        values["reference"] = reference

    payment_method = _extract_payment_method_slot(compact)
    if payment_method:
        values["payment_method"] = payment_method

    shipping_context = _extract_shipping_context_slot(compact)
    if shipping_context:
        values["shipping_context"] = shipping_context

    channel = _extract_channel_slot(compact)
    if channel:
        values["channel"] = channel

    error_context = _extract_error_context_slot(message, compact)
    if error_context:
        values["error_context"] = error_context

    impact = _extract_impact_slot(compact)
    if impact:
        values["impact"] = impact

    user_role = _extract_user_role_slot(compact)
    if user_role:
        values["user_role"] = user_role

    required_slots = set(_intake_rule_for_area(area)["required"])
    return {slot: value for slot, value in values.items() if slot in required_slots}


def _merge_session_slot_values(session: IntakeSession, message: str) -> None:
    extracted = _extract_slot_values(session.area, message)
    for slot, value in extracted.items():
        if value and not session.slot_values.get(slot):
            session.slot_values[slot] = value
    session.collected_text = _shorten(f"{session.collected_text} | {message}".strip(" |"), max_len=700)
    session.updated_at = _now_utc()


def _intake_progress(area: str, slot_values: dict[str, str]) -> tuple[list[str], float, bool]:
    rule = _intake_rule_for_area(area)
    required_slots: tuple[str, ...] = rule["required"]
    mandatory_slots: tuple[str, ...] = rule["mandatory"]
    threshold: float = rule["threshold"]

    present_count = sum(1 for slot in required_slots if slot_values.get(slot))
    ratio = present_count / max(len(required_slots), 1)
    missing = [slot for slot in required_slots if not slot_values.get(slot)]
    mandatory_ok = all(slot_values.get(slot) for slot in mandatory_slots)
    ready = mandatory_ok and ratio >= threshold
    return missing, ratio, ready


def _build_intake_missing_reply(area: str, missing_slots: list[str], ratio: float) -> str:
    lines = [
        "Perfecto, antes de crear tu ticket necesito algunos datos para derivarlo correctamente:",
        f"- Area detectada: *{area}*",
        f"- Completitud actual: *{int(ratio * 100)}%*",
        "*Datos faltantes:*",
    ]
    for slot in missing_slots:
        label = INTAKE_SLOT_LABELS.get(slot, slot)
        lines.append(f"- {label}")
    lines.append("Si no tienes un dato, indicalo igual y avanzamos.")
    return "\n".join(lines)


def _build_intake_confirmation_reply(area: str, slot_values: dict[str, str], summary: str, ratio: float) -> str:
    lines = [
        "*Confirmacion de ticket*",
        f"- Area: *{area}*",
        f"- Completitud: *{int(ratio * 100)}%*",
        f"- Resumen propuesto: {_shorten(summary, max_len=220)}",
        "*Datos capturados:*",
    ]

    for slot in _intake_rule_for_area(area)["required"]:
        value = slot_values.get(slot)
        if value:
            lines.append(f"- {INTAKE_SLOT_LABELS.get(slot, slot)}: {_shorten(value, max_len=90)}")

    lines.append("Responde *SI* para crear el ticket con esta informacion o envia mas detalles.")
    return "\n".join(lines)


def _is_affirmative_confirmation(message: str) -> bool:
    compact = " ".join(_normalize_text(message).split())
    if compact in {"si", "ok", "dale", "confirmo", "adelante", "procede"}:
        return True
    return "si crear" in compact or "crear ticket" in compact or "confirmar ticket" in compact


def _is_negative_confirmation(message: str) -> bool:
    compact = " ".join(_normalize_text(message).split())
    return compact in {"no", "aun no", "todavia no", "espera", "cancelar", "cancela"}


def _wants_cancel_intake(message: str) -> bool:
    compact = " ".join(_normalize_text(message).split())
    return compact in {
        "cancelar",
        "cancela",
        "mejor no",
        "olvidalo",
        "olvidalo por ahora",
    }


def _build_intake_summary(session: IntakeSession) -> str:
    parts = [session.summary_seed.strip()]
    for slot in _intake_rule_for_area(session.area)["required"]:
        value = session.slot_values.get(slot)
        if value:
            label = INTAKE_SLOT_LABELS.get(slot, slot)
            parts.append(f"{label}: {value}")
    summary = " | ".join(part for part in parts if part)
    return _shorten(summary, max_len=760)


def _create_ticket_from_intake(phone: str, open_tickets: list[TicketModel], session: IntakeSession) -> AgentProcessOut:
    if len(open_tickets) >= MAX_OPEN_TICKETS:
        return AgentProcessOut(
            action="no_action",
            ticket_id=open_tickets[0].id,
            area=open_tickets[0].area,
            summary=open_tickets[0].summary,
            wa_link=f"https://wa.me/{''.join(ch for ch in phone if ch.isdigit())}",
            reply_message=_build_close_ticket_options_message(open_tickets),
        )

    ticket = create_ticket(phone, area=session.area, summary=_build_intake_summary(session))
    _clear_intake_session(phone)
    return AgentProcessOut(
        action="create_ticket",
        ticket_id=ticket.id,
        area=ticket.area,
        summary=ticket.summary,
        wa_link=f"https://wa.me/{''.join(ch for ch in ticket.user_phone if ch.isdigit())}",
        reply_message=_build_ticket_reply("create_ticket", ticket),
    )


def _handle_existing_intake_session(payload: AgentProcessIn, open_tickets: list[TicketModel]) -> AgentProcessOut | None:
    session = _get_intake_session(payload.phone)
    if session is None:
        return None

    if _wants_cancel_intake(payload.message):
        _clear_intake_session(payload.phone)
        return AgentProcessOut(
            action="no_action",
            reply_message="Entendido. No creare ticket por ahora. Cuando quieras, cuentame el problema y empezamos de nuevo.",
        )

    if _is_negative_confirmation(payload.message):
        session.awaiting_confirmation = False
        _merge_session_slot_values(session, payload.message)
        _upsert_intake_session(payload.phone, session)
        return AgentProcessOut(
            action="no_action",
            reply_message="Perfecto, cuentame un poco mas del caso y completo tu ticket antes de crearlo.",
        )

    if session.awaiting_confirmation and _is_affirmative_confirmation(payload.message):
        return _create_ticket_from_intake(payload.phone, open_tickets, session)

    _merge_session_slot_values(session, payload.message)
    missing_slots, ratio, ready = _intake_progress(session.area, session.slot_values)
    if ready:
        session.awaiting_confirmation = True
        _upsert_intake_session(payload.phone, session)
        return AgentProcessOut(
            action="no_action",
            reply_message=_build_intake_confirmation_reply(
                session.area,
                session.slot_values,
                _build_intake_summary(session),
                ratio,
            ),
        )

    session.awaiting_confirmation = False
    _upsert_intake_session(payload.phone, session)
    return AgentProcessOut(
        action="no_action",
        reply_message=_build_intake_missing_reply(session.area, missing_slots, ratio),
    )


def _start_intake_for_new_ticket(payload: AgentProcessIn, area: str, summary_seed: str) -> AgentProcessOut:
    session = _get_intake_session(payload.phone) or IntakeSession(area=area, summary_seed=summary_seed)
    if session.area != area:
        session.slot_values = {}
        session.collected_text = ""
        session.awaiting_confirmation = False
    session.area = area
    if summary_seed.strip():
        session.summary_seed = summary_seed.strip()
    _merge_session_slot_values(session, payload.message)

    missing_slots, ratio, ready = _intake_progress(area, session.slot_values)
    if ready:
        session.awaiting_confirmation = True
        _upsert_intake_session(payload.phone, session)
        return AgentProcessOut(
            action="no_action",
            reply_message=_build_intake_confirmation_reply(
                area,
                session.slot_values,
                _build_intake_summary(session),
                ratio,
            ),
        )

    session.awaiting_confirmation = False
    _upsert_intake_session(payload.phone, session)
    return AgentProcessOut(
        action="no_action",
        reply_message=_build_intake_missing_reply(area, missing_slots, ratio),
    )


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    folded = unicodedata.normalize("NFKD", lowered).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9\s]", " ", folded)


def _is_greeting_only(message: str) -> bool:
    normalized = _normalize_text(message)
    compact = " ".join(normalized.split())
    if not compact:
        return False

    greeting_phrases = {
        "hola",
        "holi",
        "buenas",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "hello",
        "hi",
    }
    if compact in greeting_phrases:
        return True

    words = compact.split()
    if len(words) <= 3 and any(phrase in compact for phrase in greeting_phrases):
        return True

    return False


def _is_out_of_scope_consultation(message: str) -> bool:
    normalized = _normalize_text(message)
    compact = " ".join(normalized.split())
    if not compact:
        return False

    marketplace_scope_signals = (
        "marketplace",
        "plataforma",
        "app",
        "web",
        "pedido",
        "envio",
        "entrega",
        "tracking",
        "pago",
        "cobro",
        "reembolso",
        "factura",
        "compra",
        "venta",
        "carrito",
        "checkout",
        "cuenta",
        "login",
        "usuario",
        "artesano",
        "comprador",
        "reclamo",
        "devolucion",
        "ticket",
    )
    has_marketplace_scope = any(signal in compact for signal in marketplace_scope_signals)

    marketplace_incident_signals = (
        "no puedo",
        "no funciona",
        "error",
        "falla",
        "falla",
        "demora",
        "rechaz",
        "duplic",
        "bloque",
        "cancel",
        "devolu",
        "reembolso",
        "reclamo",
        "problema",
        "incidencia",
        "ayuda",
    )
    has_marketplace_incident = has_marketplace_scope and any(
        signal in compact for signal in marketplace_incident_signals
    )

    coding_help_signals = (
        "fibonacci",
        "fibon",
        "python",
        "javascript",
        "java",
        "codigo",
        "codig",
        "programacion",
        "programar",
        "program",
        "algoritmo",
        "algorit",
        "ejemplo",
        "dame",
        "ensename",
        "ense",
        "sql",
        "html",
        "css",
        "debug",
    )
    if any(signal in compact for signal in coding_help_signals):
        return True

    personal_or_non_operational_signals = (
        "salud",
        "enfermedad",
        "medico",
        "familia",
        "pareja",
        "novia",
        "novio",
        "hijo",
        "hija",
        "depresion",
        "ansiedad",
        "deuda",
        "finanzas personales",
        "inversion",
        "impuestos personales",
        "legal",
        "abogado",
    )
    if any(signal in compact for signal in personal_or_non_operational_signals) and not has_marketplace_scope:
        return True

    if has_marketplace_incident:
        return False

    general_consultation_signals = (
        "precio",
        "precios",
        "catalogo",
        "producto",
        "productos",
        "artesano",
        "artesanos",
        "comprar",
        "compra",
        "vende",
        "vender",
        "marketplace",
        "informacion",
        "consulta",
        "quienes son",
        "que es",
        "como funciona",
    )
    has_question_shape = "?" in message or compact.startswith(("como", "que", "cual", "donde", "quien"))

    if has_question_shape and any(signal in compact for signal in general_consultation_signals):
        return True

    # Safety-first: if there is no clear marketplace incident, treat it as out-of-scope.
    return not has_marketplace_incident


def _build_out_of_scope_reply() -> str:
    return (
        "Gracias por escribirnos. No puedo ayudar con esa consulta. "
        "Soy Pueblo Agent y solo gestiono incidencias operativas de Pueblo Lindo "
        "para derivarlas al area correcta. "
        "Si tienes un problema con pagos, envios, pedidos, cuenta o reclamos del marketplace, "
        "cuentamelo y te ayudo de inmediato."
    )


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
        "*Limite de tickets abiertos alcanzado*",
        f"Tienes *{MAX_OPEN_TICKETS}* tickets abiertos.",
        "Para abrir un ticket nuevo, primero cierra uno enviando: *CERRAR <numero>*",
        "*Tickets abiertos:*",
    ]
    for idx, ticket in enumerate(open_tickets, start=1):
        lines.append(f"{idx}) *ID:* {ticket.id}")
        lines.append(f"   *Resumen:* {_summary_title(ticket.summary)}")
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
    if action == "no_action":
        normalized_reason = _normalize_text(reason or "")
        if any(signal in normalized_reason for signal in ("saludo", "greeting", "hola")):
            return "Hola, soy Pueblo Agent de Pueblo Lindo. ¿En que puedo ayudarte hoy?"
        if any(
            signal in normalized_reason
            for signal in ("fuera", "alcance", "consulta", "program", "incidencia", "marketplace")
        ):
            return _build_out_of_scope_reply()
        return "Gracias por escribirnos. ¿Puedes contarme un poco mas de tu caso para ayudarte mejor?"

    if ticket is None:
        return "Gracias por escribirnos. ¿En que puedo ayudarte hoy?"

    if action == "create_ticket":
        return (
            "*Ticket creado*\n"
            f"- *ID:* {ticket.id}\n"
            f"- *Area:* {ticket.area}\n"
            f"- *Resumen:* {ticket.summary}"
        )
    if action == "update_ticket":
        return (
            "*Ticket actualizado*\n"
            f"- *ID:* {ticket.id}\n"
            f"- *Area:* {ticket.area}\n"
            f"- *Resumen:* {ticket.summary}"
        )
    return "Gracias por escribirnos. ¿En que puedo ayudarte hoy?"


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

    pending_intake = _handle_existing_intake_session(payload, open_tickets)
    if pending_intake is not None:
        return pending_intake

    if _is_greeting_only(payload.message):
        return AgentProcessOut(
            action="no_action",
            reply_message="Hola, soy Pueblo Agent de Pueblo Lindo. ¿En que puedo ayudarte hoy?",
        )

    if _is_out_of_scope_consultation(payload.message):
        return AgentProcessOut(
            action="no_action",
            reply_message=_build_out_of_scope_reply(),
        )

    decision: AgentDecision
    if settings.gemini_api_key:
        try:
            decision = await _decide_with_llm(payload=payload, open_tickets=open_tickets, recent_messages=recent_messages)
        except Exception as exc:
            logger.warning("agent_llm_failed err=%s", exc)
            return AgentProcessOut(
                action="no_action",
                reply_message=LLM_UNAVAILABLE_MESSAGE,
            )
    else:
        return AgentProcessOut(
            action="no_action",
            reply_message=LLM_UNAVAILABLE_MESSAGE,
        )

    if decision.action in {"create_ticket", "update_ticket"} and _is_out_of_scope_consultation(payload.message):
        return AgentProcessOut(
            action="no_action",
            reply_message=_build_out_of_scope_reply(),
        )

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
        return _start_intake_for_new_ticket(
            payload,
            decision.create_ticket.area,
            decision.create_ticket.summary,
        )

    if decision.action == "update_ticket" and decision.update_ticket is not None:
        target_id: UUID = decision.update_ticket.ticket_id
        open_ticket_by_id = {ticket.id: ticket for ticket in open_tickets}
        target = open_ticket_by_id.get(target_id)
        if target is None and open_tickets:
            target = open_tickets[0]
            target_id = target.id

        if target is None:
            return _start_intake_for_new_ticket(
                payload,
                decision.update_ticket.area,
                decision.update_ticket.summary,
            )

        merged = _merge_summaries(target.summary, decision.update_ticket.summary)
        updated = update_open_ticket_summary(
            target_id,
            decision.update_ticket.area,
            merged,
        )
        if updated is None:
            return _start_intake_for_new_ticket(
                payload,
                decision.update_ticket.area,
                decision.update_ticket.summary,
            )

        return AgentProcessOut(
            action="update_ticket",
            ticket_id=updated.id,
            area=updated.area,
            summary=updated.summary,
            wa_link=f"https://wa.me/{''.join(ch for ch in updated.user_phone if ch.isdigit())}",
            reply_message=_build_ticket_reply("update_ticket", updated),
        )

    no_action_reason = decision.no_action.reason if decision.no_action else None
    return AgentProcessOut(
        action="no_action",
        reply_message=_build_ticket_reply("no_action", None, no_action_reason),
    )
