from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AgentProcessIn(BaseModel):
    phone: str = Field(min_length=8, max_length=30)
    message: str = Field(min_length=1, max_length=4096)
    external_message_id: str = Field(min_length=1, max_length=512)
    event: str = "message.received"


class OpenTicketContext(BaseModel):
    id: UUID
    area: str
    summary: str
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime


class RecentMessageContext(BaseModel):
    sender: Literal["user", "agent"]
    content: str
    created_at: datetime


class CreateTicketToolInput(BaseModel):
    area: Literal["soporte_tecnico", "pagos", "envios", "reclamos", "ventas", "otros"]
    summary: str = Field(min_length=10, max_length=800)


class CreateTicketToolOutput(BaseModel):
    ticket_id: UUID
    area: str
    summary: str


class UpdateTicketSummaryToolInput(BaseModel):
    ticket_id: UUID
    area: Literal["soporte_tecnico", "pagos", "envios", "reclamos", "ventas", "otros"]
    summary: str = Field(min_length=10, max_length=800)
    reason: str = Field(min_length=5, max_length=400)


class UpdateTicketSummaryToolOutput(BaseModel):
    ticket_id: UUID
    area: str
    summary: str


class NoActionToolInput(BaseModel):
    reason: str = Field(min_length=5, max_length=400)


class AgentDecision(BaseModel):
    action: Literal["create_ticket", "update_ticket", "no_action"]
    create_ticket: CreateTicketToolInput | None = None
    update_ticket: UpdateTicketSummaryToolInput | None = None
    no_action: NoActionToolInput | None = None


class AgentProcessOut(BaseModel):
    action: Literal["create_ticket", "update_ticket", "no_action"]
    ticket_id: UUID | None = None
    area: str | None = None
    summary: str | None = None
    wa_link: str | None = None
    reply_message: str
