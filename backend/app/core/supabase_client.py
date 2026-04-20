from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Any:
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY for Supabase backend")

    try:
        from supabase import create_client
    except Exception as exc:  # pragma: no cover - import guard for optional dependency
        raise RuntimeError(
            "supabase package is not installed. Add it to requirements and install dependencies."
        ) from exc

    return create_client(settings.supabase_url, settings.supabase_key)


def validate_supabase_settings() -> None:
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")
