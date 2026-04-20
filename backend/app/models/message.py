from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class MessageModel:
    id: UUID
    ticket_id: UUID
    external_message_id: str | None
    sender: str
    content: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: Mapping[str, str | None]) -> "MessageModel":
        return cls(
            id=UUID(row["id"]),
            ticket_id=UUID(row["ticket_id"]),
            external_message_id=row["external_message_id"],
            sender=row["sender"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
