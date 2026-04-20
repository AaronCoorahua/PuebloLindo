from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class TicketModel:
    id: UUID
    user_phone: str
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Mapping[str, str]) -> "TicketModel":
        return cls(
            id=UUID(row["id"]),
            user_phone=row["user_phone"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
