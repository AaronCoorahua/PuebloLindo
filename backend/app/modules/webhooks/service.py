from __future__ import annotations

import logging

from fastapi import HTTPException

from app.core.config import settings
from app.modules.messages.schemas import SendMessageIn
from app.modules.messages.service import send_outbound_message
from app.modules.tickets.service import create_message, get_or_create_open_ticket
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


def _extract_external_message_id(payload: WhatsAppWebhookIn) -> str:
    nested = payload.data if isinstance(payload.data, dict) else None
    value = (
        payload.external_message_id
        or payload.message_id
        or _pick(nested, "external_message_id", "message_id", "id")
    )
    if not value:
        raise HTTPException(status_code=422, detail="external_message_id/message_id is required")
    return value


def _extract_phone(payload: WhatsAppWebhookIn) -> str:
    nested = payload.data if isinstance(payload.data, dict) else None
    value = payload.phone or payload.from_phone or _pick(nested, "phone", "from", "from_phone")
    if not value:
        raise HTTPException(status_code=422, detail="phone/from is required")
    return value


def _extract_content(payload: WhatsAppWebhookIn) -> str:
    nested = payload.data if isinstance(payload.data, dict) else None
    value = payload.message or payload.text or payload.content or _pick(nested, "message", "text", "content")
    if not value:
        raise HTTPException(status_code=422, detail="message/text/content is required")
    return value


async def process_whatsapp_webhook(payload: WhatsAppWebhookIn) -> WebhookAckOut:
    external_message_id = _extract_external_message_id(payload)
    user_phone = _extract_phone(payload)
    user_message = _extract_content(payload)

    ticket = get_or_create_open_ticket(user_phone=user_phone)
    _, created = create_message(
        ticket_id=ticket.id,
        sender="user",
        content=user_message,
        external_message_id=external_message_id,
        created_at=payload.timestamp,
    )

    if not created:
        logger.info(
            "webhook_idempotent event_id=%s ticket_id=%s phone=%s",
            external_message_id,
            ticket.id,
            user_phone,
        )
        return WebhookAckOut(
            received=True,
            event_id=external_message_id,
            ticket_id=ticket.id,
            idempotent=True,
        )

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
