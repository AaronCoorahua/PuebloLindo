from fastapi import FastAPI

from app.core.config import settings
from app.core.cors import configure_cors
from app.core.db import init_db
from app.modules.health.router import router as health_router
from app.modules.messages.router import router as messages_router
from app.modules.tickets.router import router as tickets_router
from app.modules.webhooks.router import router as webhooks_router

app = FastAPI(title=settings.app_name)
configure_cors(app, settings.frontend_origin)
app.include_router(health_router)
app.include_router(webhooks_router, prefix=settings.api_v1_prefix)
app.include_router(messages_router, prefix=settings.api_v1_prefix)
app.include_router(tickets_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
async def startup_event() -> None:
    init_db()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
