from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

class TicketOut(BaseModel):
    id: UUID
    user_phone: str
    status: Literal["open", "closed"]
    area: str
    summary: str
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime
    wa_link: str


class TicketDetailOut(BaseModel):
    ticket: TicketOut


class TicketListOut(BaseModel):
    items: list[TicketOut]
    total: int
    limit: int
    offset: int


class CloseTicketOut(BaseModel):
    ticket: TicketOut
