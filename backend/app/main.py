from fastapi import FastAPI

from app.core.config import settings
from app.core.cors import configure_cors
from app.modules.health.router import router as health_router

app = FastAPI(title=settings.app_name)
configure_cors(app, settings.frontend_origin)
app.include_router(health_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
