from pydantic_settings import BaseSettings, SettingsConfigDict  # ✅ IMPORT CORRETTO

class Settings(BaseSettings):
    scheduler_interval_minutes: int = 10
    firebase_server_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore"  # 🔥 ignora variabili extra (es. DB_USER ecc.)
    )

# Istanza globale
settings = Settings()
