from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.modules.messages.schemas import SendMessageIn
from app.modules.messages.service import send_outbound_message
from app.modules.tickets.service import get_or_create_open_ticket
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
    user_phone = _extract_phone(payload)
    _extract_content(payload)

    ticket = get_or_create_open_ticket(user_phone=user_phone)

    logger.info(
        "webhook_received event_id=%s ticket_id=%s phone=%s",
        external_message_id,
        ticket.id,
        user_phone,
    )

    await send_outbound_message(
        SendMessageIn(phone=user_phone, message=settings.auto_reply_text)
    )

    return WebhookAckOut(
        received=True,
        event_id=external_message_id,
        ticket_id=ticket.id,
        idempotent=False,
    )
