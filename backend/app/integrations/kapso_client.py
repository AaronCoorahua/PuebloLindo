from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import httpx

from app.core.config import settings


@dataclass(slots=True)
class KapsoSendResult:
    sent: bool
    provider_message_id: str


async def send_text_message(phone: str, message: str) -> KapsoSendResult:
    if settings.kapso_mock_mode:
        return KapsoSendResult(sent=True, provider_message_id=f"mock-{uuid4()}")

    if not settings.kapso_api_key:
        raise ValueError("KAPSO_API_KEY is required when kapso_mock_mode is disabled")

    url = f"{settings.kapso_base_url.rstrip('/')}{settings.kapso_send_path}"
    payload = {
        "to": phone,
        "type": "text",
        "text": {"body": message},
    }
    headers = {
        "Authorization": f"Bearer {settings.kapso_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json() if response.content else {}

    provider_message_id = (
        data.get("id")
        or data.get("message_id")
        or data.get("wamid")
        or f"kapso-{uuid4()}"
    )
    return KapsoSendResult(sent=True, provider_message_id=provider_message_id)
