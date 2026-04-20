from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    raise ValueError(f"Invalid datetime value for ticket: {value!r}")


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
        updated_raw = row.get("updated_at")
        if updated_raw is None:
            raise ValueError("Ticket row missing updated_at")

        created_raw = row.get("created_at") or updated_raw
        last_activity_raw = row.get("last_activity_at") or updated_raw

        return cls(
            id=UUID(row["id"]),
            user_phone=row["user_phone"],
            status=row["status"],
            area=row.get("area") or "otros",
            summary=row.get("summary") or "",
            created_at=_parse_datetime(created_raw),
            updated_at=_parse_datetime(updated_raw),
            last_activity_at=_parse_datetime(last_activity_raw),
        )
