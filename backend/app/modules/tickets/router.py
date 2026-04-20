from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.modules.tickets.schemas import CloseTicketOut, TicketDetailOut, TicketListOut
from app.modules.tickets.service import close_ticket, get_ticket_detail, list_tickets

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=TicketListOut)
async def get_tickets(
    status: Literal["open", "closed"] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TicketListOut:
    return list_tickets(status=status, limit=limit, offset=offset)


@router.get("/{ticket_id}", response_model=TicketDetailOut)
async def get_ticket(ticket_id: UUID) -> TicketDetailOut:
    ticket = get_ticket_detail(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/{ticket_id}/close", response_model=CloseTicketOut)
async def close_ticket_endpoint(ticket_id: UUID) -> CloseTicketOut:
    result = close_ticket(ticket_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return result
