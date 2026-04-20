from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.modules.webhooks.schemas import WebhookAckOut
from app.modules.webhooks.service import process_whatsapp_webhook_raw

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/whatsapp", response_model=WebhookAckOut)
async def receive_whatsapp_webhook(request: Request) -> WebhookAckOut:
    payload: Any = await request.json()
    webhook_event = request.headers.get("X-Webhook-Event")
    return await process_whatsapp_webhook_raw(payload, webhook_event=webhook_event)
