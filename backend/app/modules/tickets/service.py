from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.supabase_client import get_supabase_client
from app.models.ticket import TicketModel
from app.modules.tickets.schemas import CloseTicketOut, TicketDetailOut, TicketListOut, TicketOut


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ticket_to_out(ticket: TicketModel) -> TicketOut:
    return TicketOut(
        id=ticket.id,
        user_phone=ticket.user_phone,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def _ticket_from_dict(row: dict[str, Any]) -> TicketModel:
    return TicketModel(
        id=UUID(row["id"]),
        user_phone=row["user_phone"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _get_ticket_by_phone_with_status(user_phone: str, status: str) -> TicketModel | None:
    client = get_supabase_client()
    table = settings.supabase_tickets_table
    response = (
        client.table(table)
        .select("*")
        .eq("user_phone", user_phone)
        .eq("status", status)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = response.data or []
    if not data:
        return None
    return _ticket_from_dict(data[0])


def _get_ticket_by_id(ticket_id: UUID) -> TicketModel | None:
    client = get_supabase_client()
    table = settings.supabase_tickets_table
    response = client.table(table).select("*").eq("id", str(ticket_id)).limit(1).execute()
    data = response.data or []
    if not data:
        return None
    return _ticket_from_dict(data[0])


def create_ticket(user_phone: str) -> TicketModel:
    now = _now_utc()
    ticket_id = uuid4()

    client = get_supabase_client()
    table = settings.supabase_tickets_table
    payload = {
        "id": str(ticket_id),
        "user_phone": user_phone,
        "status": "open",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    response = client.table(table).insert(payload).execute()
    data = response.data or []
    if not data:
        raise RuntimeError("Ticket could not be created")
    return _ticket_from_dict(data[0])


def get_or_create_open_ticket(user_phone: str) -> TicketModel:
    existing = _get_ticket_by_phone_with_status(user_phone=user_phone, status="open")
    if existing is not None:
        return existing
    return create_ticket(user_phone=user_phone)


def list_tickets(status: str | None, limit: int, offset: int) -> TicketListOut:
    client = get_supabase_client()
    table = settings.supabase_tickets_table
    query = client.table(table).select("*", count="exact")

    if status is not None:
        query = query.eq("status", status)

    end = offset + limit - 1
    response = query.order("created_at", desc=True).range(offset, end).execute()
    rows = response.data or []
    total = int(response.count or 0)
    items = [_ticket_to_out(_ticket_from_dict(row)) for row in rows]
    return TicketListOut(items=items, total=total, limit=limit, offset=offset)


def get_ticket_detail(ticket_id: UUID) -> TicketDetailOut | None:
    ticket = _get_ticket_by_id(ticket_id)
    if ticket is None:
        return None
    return TicketDetailOut(ticket=_ticket_to_out(ticket))


def close_ticket(ticket_id: UUID) -> CloseTicketOut | None:
    now = _now_utc()

    client = get_supabase_client()
    table = settings.supabase_tickets_table
    update_response = (
        client.table(table)
        .update({"status": "closed", "updated_at": now.isoformat()})
        .eq("id", str(ticket_id))
        .execute()
    )

    data = update_response.data or []
    if not data:
        return None

    return CloseTicketOut(ticket=_ticket_to_out(_ticket_from_dict(data[0])))
