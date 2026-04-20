from __future__ import annotations

from fastapi import APIRouter

from app.modules.agent.schemas import AgentProcessIn, AgentProcessOut
from app.modules.agent.service import run_ticket_agent

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/process", response_model=AgentProcessOut)
async def process_agent(payload: AgentProcessIn) -> AgentProcessOut:
    return await run_ticket_agent(payload)
