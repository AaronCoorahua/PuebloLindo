from __future__ import annotations

import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Query

from app.modules.messages.service import send_outbound_message_for_ticket
from app.modules.tickets.schemas import CloseTicketIn, CloseTicketOut, TicketDetailOut, TicketListOut
from app.modules.tickets.service import close_ticket, get_ticket_by_id, get_ticket_detail, list_tickets

router = APIRouter(prefix="/tickets", tags=["tickets"])
logger = logging.getLogger(__name__)


def _raise_backend_unavailable(exc: Exception) -> None:
    logger.exception("tickets_backend_unavailable err=%s", exc)
    raise HTTPException(
        status_code=503,
        detail="No se pudo conectar a Supabase. Verifica SUPABASE_URL y SUPABASE_KEY en backend/.env.",
    ) from exc


@router.get("", response_model=TicketListOut)
async def get_tickets(
    status: Literal["open", "closed"] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TicketListOut:
    try:
        return list_tickets(status=status, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as exc:
        _raise_backend_unavailable(exc)


@router.get("/{ticket_id}", response_model=TicketDetailOut)
async def get_ticket(ticket_id: UUID) -> TicketDetailOut:
    try:
        ticket = get_ticket_detail(ticket_id)
    except HTTPException:
        raise
    except Exception as exc:
        _raise_backend_unavailable(exc)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/{ticket_id}/close", response_model=CloseTicketOut)
async def close_ticket_endpoint(
    ticket_id: UUID,
    payload: CloseTicketIn | None = Body(default=None),
) -> CloseTicketOut:
    try:
        current = get_ticket_by_id(ticket_id)
    except HTTPException:
        raise
    except Exception as exc:
        _raise_backend_unavailable(exc)

    if current is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        result = close_ticket(
            ticket_id,
            closed_by=payload.atendedor if payload is not None else None,
            closed_message=payload.mensaje_cierre if payload is not None else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_backend_unavailable(exc)

    if result is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if payload is None:
        return result

    close_message = (
        "*Ticket cerrado*\n"
        f"- Ticket ID: *{result.ticket.id}*\n"
        f"- Cerrado por: *{payload.atendedor}*\n"
        f"- Mensaje: *{payload.mensaje_cierre}*"
    )

    try:
        await send_outbound_message_for_ticket(
            phone=result.ticket.user_phone,
            message=close_message,
            ticket_id=result.ticket.id,
        )
        return CloseTicketOut(ticket=result.ticket, notification_sent=True)
    except Exception as exc:
        logger.warning("ticket_close_notification_failed ticket_id=%s err=%s", ticket_id, exc)
        return CloseTicketOut(
            ticket=result.ticket,
            notification_sent=False,
            notification_error="No se pudo enviar el mensaje de cierre al usuario.",
        )
