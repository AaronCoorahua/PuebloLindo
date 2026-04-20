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


def _to_wa_link(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"https://api.whatsapp.com/send?phone={digits}&text=Hola!"


def _ticket_to_out(ticket: TicketModel) -> TicketOut:
    return TicketOut(
        id=ticket.id,
        user_phone=ticket.user_phone,
        status=ticket.status,
        area=ticket.area,
        title=ticket.title,
        summary=ticket.summary,
        closed_by=ticket.closed_by,
        closed_message=ticket.closed_message,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        last_activity_at=ticket.last_activity_at,
        wa_link=_to_wa_link(ticket.user_phone),
    )


def _ticket_from_dict(row: dict[str, Any]) -> TicketModel:
    return TicketModel.from_row(row)


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


def list_open_tickets_for_phone(user_phone: str, limit: int = 20) -> list[TicketModel]:
    client = get_supabase_client()
    table = settings.supabase_tickets_table
    response = (
        client.table(table)
        .select("*")
        .eq("user_phone", user_phone)
        .eq("status", "open")
        .order("last_activity_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = response.data or []
    return [_ticket_from_dict(row) for row in rows]


def _get_ticket_by_id(ticket_id: UUID) -> TicketModel | None:
    client = get_supabase_client()
    table = settings.supabase_tickets_table
    response = client.table(table).select("*").eq("id", str(ticket_id)).limit(1).execute()
    data = response.data or []
    if not data:
        return None
    return _ticket_from_dict(data[0])


def get_ticket_by_id(ticket_id: UUID) -> TicketModel | None:
    return _get_ticket_by_id(ticket_id)


def create_ticket(user_phone: str, area: str = "otros", title: str = "", summary: str = "") -> TicketModel:
    now = _now_utc()
    ticket_id = uuid4()

    client = get_supabase_client()
    table = settings.supabase_tickets_table
    payload = {
        "id": str(ticket_id),
        "user_phone": user_phone,
        "status": "open",
        "area": area,
        "title": title,
        "summary": summary,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "last_activity_at": now.isoformat(),
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


def update_open_ticket_summary(ticket_id: UUID, area: str, summary: str, title: str | None = None) -> TicketModel | None:
    now = _now_utc()

    client = get_supabase_client()
    table = settings.supabase_tickets_table
    update_payload: dict[str, str] = {
        "area": area,
        "summary": summary,
        "updated_at": now.isoformat(),
        "last_activity_at": now.isoformat(),
    }
    if title is not None:
        update_payload["title"] = title

    response = (
        client.table(table)
        .update(update_payload)
        .eq("id", str(ticket_id))
        .eq("status", "open")
        .execute()
    )
    data = response.data or []
    if not data:
        return None
    return _ticket_from_dict(data[0])


def touch_open_ticket_activity(ticket_id: UUID) -> TicketModel | None:
    now = _now_utc()
    client = get_supabase_client()
    table = settings.supabase_tickets_table
    response = (
        client.table(table)
        .update(
            {
                "updated_at": now.isoformat(),
                "last_activity_at": now.isoformat(),
            }
        )
        .eq("id", str(ticket_id))
        .eq("status", "open")
        .execute()
    )
    data = response.data or []
    if not data:
        return None
    return _ticket_from_dict(data[0])


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


def close_ticket(ticket_id: UUID, closed_by: str | None = None, closed_message: str | None = None) -> CloseTicketOut | None:
    now = _now_utc()

    client = get_supabase_client()
    table = settings.supabase_tickets_table
    update_payload: dict[str, str] = {
        "status": "closed",
        "updated_at": now.isoformat(),
    }
    if closed_by is not None:
        update_payload["closed_by"] = closed_by
    if closed_message is not None:
        update_payload["closed_message"] = closed_message

    update_response = (
        client.table(table)
        .update(update_payload)
        .eq("id", str(ticket_id))
        .execute()
    )

    data = update_response.data or []
    if not data:
        return None

    return CloseTicketOut(ticket=_ticket_to_out(_ticket_from_dict(data[0])))
