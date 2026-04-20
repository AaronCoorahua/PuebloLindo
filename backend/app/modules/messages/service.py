from __future__ import annotations

from app.integrations.kapso_client import send_text_message
from app.modules.messages.schemas import SendMessageIn, SendMessageOut
from app.modules.tickets.service import get_or_create_open_ticket


async def send_outbound_message(payload: SendMessageIn) -> SendMessageOut:
    ticket = get_or_create_open_ticket(payload.phone)
    kapso_result = await send_text_message(phone=payload.phone, message=payload.message)

    return SendMessageOut(
        sent=kapso_result.sent,
        provider_message_id=kapso_result.provider_message_id,
        ticket_id=ticket.id,
    )
