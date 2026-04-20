from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class MessageOut(BaseModel):
    id: UUID
    ticket_id: UUID
    external_message_id: str | None
    sender: Literal["user", "system"]
    content: str
    created_at: datetime


class TicketOut(BaseModel):
    id: UUID
    user_phone: str
    status: Literal["open", "closed"]
    created_at: datetime
    updated_at: datetime


class TicketDetailOut(BaseModel):
    ticket: TicketOut
    messages: list[MessageOut]


class TicketListOut(BaseModel):
    items: list[TicketOut]
    total: int
    limit: int
    offset: int


class CloseTicketOut(BaseModel):
    ticket: TicketOut
