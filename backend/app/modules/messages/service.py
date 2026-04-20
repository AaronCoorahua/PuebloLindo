from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.supabase_client import get_supabase_client
from app.integrations.kapso_client import send_text_message
from app.models.message import MessageModel
from app.modules.messages.schemas import SendMessageIn, SendMessageOut
from app.modules.tickets.service import get_or_create_open_ticket, touch_open_ticket_activity


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _message_from_dict(row: dict[str, object]) -> MessageModel:
    return MessageModel.from_row(row)


def save_message(
    *,
    ticket_id: UUID | None,
    user_phone: str,
    sender: str,
    content: str,
    external_message_id: str | None = None,
) -> MessageModel:
    client = get_supabase_client()
    table = settings.supabase_messages_table
    now = _now_utc()
    payload = {
        "id": str(uuid4()),
        "ticket_id": str(ticket_id) if ticket_id is not None else None,
        "user_phone": user_phone,
        "external_message_id": external_message_id,
        "sender": sender,
        "content": content,
        "created_at": now.isoformat(),
    }
    response = client.table(table).insert(payload).execute()
    rows = response.data or []
    if not rows:
        raise RuntimeError("Message could not be persisted")
    return _message_from_dict(rows[0])


def find_message_by_external_id(external_message_id: str) -> MessageModel | None:
    client = get_supabase_client()
    table = settings.supabase_messages_table
    response = (
        client.table(table)
        .select("*")
        .eq("external_message_id", external_message_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return None
    return _message_from_dict(rows[0])


def list_recent_messages_by_phone(user_phone: str, limit: int) -> list[MessageModel]:
    client = get_supabase_client()
    table = settings.supabase_messages_table
    response = (
        client.table(table)
        .select("*")
        .eq("user_phone", user_phone)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = response.data or []
    messages = [_message_from_dict(row) for row in rows]
    messages.reverse()
    return messages


async def send_outbound_message_for_ticket(*, phone: str, message: str, ticket_id: UUID) -> SendMessageOut:
    kapso_result = await send_text_message(phone=phone, message=message)
    save_message(
        ticket_id=ticket_id,
        user_phone=phone,
        sender="agent",
        content=message,
        external_message_id=kapso_result.provider_message_id,
    )
    touch_open_ticket_activity(ticket_id)
    return SendMessageOut(
        sent=kapso_result.sent,
        provider_message_id=kapso_result.provider_message_id,
        ticket_id=ticket_id,
    )


async def send_outbound_message_without_ticket(*, phone: str, message: str) -> str:
    kapso_result = await send_text_message(phone=phone, message=message)
    save_message(
        ticket_id=None,
        user_phone=phone,
        sender="agent",
        content=message,
        external_message_id=kapso_result.provider_message_id,
    )
    return kapso_result.provider_message_id


async def send_outbound_message(payload: SendMessageIn) -> SendMessageOut:
    ticket = get_or_create_open_ticket(payload.phone)
    return await send_outbound_message_for_ticket(
        phone=payload.phone,
        message=payload.message,
        ticket_id=ticket.id,
    )
