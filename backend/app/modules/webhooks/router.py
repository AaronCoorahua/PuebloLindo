from __future__ import annotations

from fastapi import APIRouter

from app.modules.webhooks.schemas import WebhookAckOut, WhatsAppWebhookIn
from app.modules.webhooks.service import process_whatsapp_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/whatsapp", response_model=WebhookAckOut)
async def receive_whatsapp_webhook(payload: WhatsAppWebhookIn) -> WebhookAckOut:
    return await process_whatsapp_webhook(payload)
