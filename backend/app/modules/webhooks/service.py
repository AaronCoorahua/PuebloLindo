from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.modules.agent.schemas import AgentProcessIn
from app.modules.agent.service import run_ticket_agent
from app.modules.messages.service import (
    find_message_by_external_id,
    save_message,
    send_outbound_message_for_ticket,
    send_outbound_message_without_ticket,
)
from app.modules.tickets.service import get_or_create_open_ticket, get_ticket_by_id, list_open_tickets_for_phone
from app.modules.webhooks.schemas import WebhookAckOut, WhatsAppWebhookIn

logger = logging.getLogger(__name__)


def _pick(data: dict[str, object] | None, *keys: str) -> str | None:
    if not data:
        return None
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _find_first_str(obj: Any, keys: set[str]) -> str | None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in keys and isinstance(value, str) and value.strip():
                return value.strip()
            found = _find_first_str(value, keys)
            if found:
                return found

    if isinstance(obj, list):
        for value in obj:
            found = _find_first_str(value, keys)
            if found:
                return found

    return None


def _extract_timestamp(raw: dict[str, Any]) -> datetime | None:
    value = _find_first_str(raw, {"timestamp", "created_at", "time"})
    if value:
        if value.isdigit():
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass

    return None


def _iter_candidates(payload: Any) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    def push(item: Any) -> None:
        if isinstance(item, dict):
            candidates.append(item)
            for key in ("data", "event", "message"):
                nested = item.get(key)
                if isinstance(nested, dict):
                    candidates.append(nested)
            for key in ("events", "data", "messages", "batch", "entry"):
                nested = item.get(key)
                if isinstance(nested, list):
                    for entry in nested:
                        if isinstance(entry, dict):
                            candidates.append(entry)
                            if "changes" in entry and isinstance(entry["changes"], list):
                                for change in entry["changes"]:
                                    if isinstance(change, dict):
                                        value = change.get("value")
                                        if isinstance(value, dict):
                                            candidates.append(value)

    if isinstance(payload, list):
        for item in payload:
            push(item)
    else:
        push(payload)

    return candidates


def _normalize_payload(raw: dict[str, Any]) -> WhatsAppWebhookIn | None:
    external_message_id = _find_first_str(raw, {"external_message_id", "message_id", "id", "wamid"})
    phone = _find_first_str(raw, {"phone", "from", "from_phone", "wa_id"})
    content = _find_first_str(raw, {"message", "text", "content", "body"})

    if not external_message_id or not phone or not content:
        return None

    event_name = _find_first_str(raw, {"event", "type"}) or "message.received"
    return WhatsAppWebhookIn(
        event=event_name,
        external_message_id=external_message_id,
        phone=phone,
        message=content,
        timestamp=_extract_timestamp(raw),
        data=raw,
    )


def _extract_external_message_id(payload: WhatsAppWebhookIn) -> str:
    nested = payload.data if isinstance(payload.data, dict) else None
    value = (
        payload.external_message_id
        or payload.message_id
        or _pick(nested, "wamid")
        or _pick(nested, "external_message_id", "message_id", "id")
    )
    if not value:
        raise ValueError("external_message_id/message_id is required")
    return value


def _extract_phone(payload: WhatsAppWebhookIn) -> str:
    nested = payload.data if isinstance(payload.data, dict) else None
    value = payload.phone or payload.from_phone or _pick(nested, "phone", "from", "from_phone", "wa_id")
    if not value:
        raise ValueError("phone/from is required")
    return value


def _extract_content(payload: WhatsAppWebhookIn) -> str:
    nested = payload.data if isinstance(payload.data, dict) else None
    value = payload.message or payload.text or payload.content or _pick(nested, "message", "text", "content", "body")
    if not value:
        raise ValueError("message/text/content is required")
    return value


async def process_whatsapp_webhook_raw(payload: Any, webhook_event: str | None = None) -> WebhookAckOut:
    candidates = _iter_candidates(payload)
    for candidate in candidates:
        normalized = _normalize_payload(candidate)
        if normalized is None:
            continue

        try:
            return await process_whatsapp_webhook(normalized)
        except ValueError:
            continue

    logger.warning("webhook_ignored event=%s payload_unprocessable", webhook_event or "unknown")
    return WebhookAckOut(received=True, event_id=f"ignored-{uuid4()}", idempotent=True)


async def process_whatsapp_webhook(payload: WhatsAppWebhookIn) -> WebhookAckOut:
    external_message_id = _extract_external_message_id(payload)
    already_processed = find_message_by_external_id(external_message_id)
    if already_processed is not None:
        return WebhookAckOut(
            received=True,
            event_id=external_message_id,
            ticket_id=already_processed.ticket_id,
            idempotent=True,
        )

    user_phone = _extract_phone(payload)
    content = _extract_content(payload)

    agent_out = await run_ticket_agent(
        AgentProcessIn(
            phone=user_phone,
            message=content,
            external_message_id=external_message_id,
            event=payload.event,
        )
    )

    # For greeting/small-talk events we can reply without forcing ticket creation.
    if agent_out.action == "no_action" and agent_out.ticket_id is None:
        save_message(
            ticket_id=None,
            user_phone=user_phone,
            sender="user",
            content=content,
            external_message_id=external_message_id,
        )
        await send_outbound_message_without_ticket(phone=user_phone, message=agent_out.reply_message)
        logger.info(
            "webhook_received_no_ticket event_id=%s phone=%s",
            external_message_id,
            user_phone,
        )
        return WebhookAckOut(
            received=True,
            event_id=external_message_id,
            ticket_id=None,
            idempotent=False,
        )

    if agent_out.ticket_id is None:
        existing = list_open_tickets_for_phone(user_phone=user_phone, limit=1)
        ticket = existing[0] if existing else get_or_create_open_ticket(user_phone=user_phone)
    else:
        ticket = get_ticket_by_id(agent_out.ticket_id) or get_or_create_open_ticket(user_phone=user_phone)

    save_message(
        ticket_id=ticket.id,
        user_phone=user_phone,
        sender="user",
        content=content,
        external_message_id=external_message_id,
    )

    await send_outbound_message_for_ticket(
        phone=user_phone,
        message=agent_out.reply_message,
        ticket_id=ticket.id,
    )

    # Send follow-up message if ticket was just created
    if agent_out.action == "create_ticket":
        await send_outbound_message_for_ticket(
            phone=user_phone,
            message="Se estarán comunicando con usted para resolver el problema, gracias por esperar.",
            ticket_id=ticket.id,
        )

    logger.info(
        "webhook_received event_id=%s ticket_id=%s phone=%s",
        external_message_id,
        ticket.id,
        user_phone,
    )

    return WebhookAckOut(
        received=True,
        event_id=external_message_id,
        ticket_id=ticket.id,
        idempotent=False,
    )
