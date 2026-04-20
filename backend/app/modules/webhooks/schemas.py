from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WhatsAppWebhookIn(BaseModel):
    event: str = "message.received"
    message_id: str | None = None
    external_message_id: str | None = None
    phone: str | None = None
    from_phone: str | None = Field(default=None, alias="from")
    message: str | None = None
    text: str | None = None
    content: str | None = None
    timestamp: datetime | None = None
    channel: str = "whatsapp"
    data: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class WebhookAckOut(BaseModel):
    received: bool
    event_id: str
    ticket_id: UUID | None = None
    idempotent: bool = False
