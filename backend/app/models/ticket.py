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
    area: str
    summary: str
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime

    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> "TicketModel":
        return cls(
            id=UUID(row["id"]),
            user_phone=row["user_phone"],
            status=row["status"],
            area=row.get("area") or "otros",
            summary=row.get("summary") or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_activity_at=datetime.fromisoformat(row.get("last_activity_at") or row["updated_at"]),
        )
