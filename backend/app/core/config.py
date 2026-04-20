from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PuebloLindo API"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:3000"

    supabase_url: str = ""
    supabase_key: str = ""
    supabase_schema: str = "public"
    supabase_tickets_table: str = "tickets"
    supabase_messages_table: str = "messages"

    kapso_base_url: str = "https://api.kapso.ai"
    kapso_api_key: str = ""
    kapso_send_path: str = "/api/meta/whatsapp/messages/send"
    kapso_mock_mode: bool = True

    auto_reply_text: str = "Hemos recibido tu mensaje. Te contactaremos pronto."

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
