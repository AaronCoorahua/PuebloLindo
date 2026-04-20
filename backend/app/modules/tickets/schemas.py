from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

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
    notification_sent: bool = False
    notification_error: str | None = None


class CloseTicketIn(BaseModel):
    mensaje_cierre: str = Field(min_length=3, max_length=1000)
    atendedor: str = Field(min_length=2, max_length=120)
