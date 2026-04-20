from __future__ import annotations

from app.core.supabase_client import validate_supabase_settings


def init_db() -> None:
    # Keep startup hook name stable while enforcing Supabase-only runtime.
    validate_supabase_settings()
