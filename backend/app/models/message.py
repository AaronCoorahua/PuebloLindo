from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class MessageModel:
    id: UUID
    ticket_id: UUID
    user_phone: str
    external_message_id: str | None
    sender: str
    content: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> "MessageModel":
        return cls(
            id=UUID(row["id"]),
            ticket_id=UUID(row["ticket_id"]),
            user_phone=str(row.get("user_phone") or ""),
            external_message_id=str(row["external_message_id"]) if row.get("external_message_id") else None,
            sender=str(row["sender"]),
            content=str(row["content"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
