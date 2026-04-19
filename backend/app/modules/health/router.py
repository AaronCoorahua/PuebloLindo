from fastapi import APIRouter

from app.modules.health.schemas import HealthResponse
from app.modules.health.service import get_health_status

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return get_health_status()
