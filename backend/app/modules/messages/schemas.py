from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SendMessageIn(BaseModel):
    phone: str = Field(min_length=8, max_length=30)
    message: str = Field(min_length=1, max_length=4096)


class SendMessageOut(BaseModel):
    sent: bool
    provider_message_id: str
    ticket_id: UUID
