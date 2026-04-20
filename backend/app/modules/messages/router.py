from __future__ import annotations

from fastapi import APIRouter

from app.modules.messages.schemas import SendMessageIn, SendMessageOut
from app.modules.messages.service import send_outbound_message

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/send", response_model=SendMessageOut)
async def send_message(payload: SendMessageIn) -> SendMessageOut:
    return await send_outbound_message(payload)
