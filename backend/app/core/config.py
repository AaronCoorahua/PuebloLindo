from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PuebloLindo API"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:3000"

    supabase_url: str = ""
    supabase_key: str = ""
    supabase_schema: str = "public"
    supabase_tickets_table: str = "tickets"

    kapso_base_url: str = "https://api.kapso.ai/meta/whatsapp/v24.0"
    kapso_api_key: str = ""
    kapso_phone_number_id: str = ""
    kapso_send_path: str = "/{phone_number_id}/messages"
    kapso_mock_mode: bool = True

    gemini_api_key: str = ""
    gemini_model_primary: str = "gemini-3.1-flash-lite-preview"
    gemini_model_fallback: str = "gemini-3-flash-preview"

    auto_reply_text: str = "Hemos recibido tu mensaje. Te contactaremos pronto."

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
