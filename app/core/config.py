from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "tk-live Admin"
    api_prefix: str = "/api"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "postgresql+psycopg://postgresql:your-password@localhost:55443/ai_db"
    cors_origins: str = "http://localhost:5174,http://127.0.0.1:5174"
    initial_admin_username: str = "admin"
    initial_admin_password: str = "admin123"
    integration_api_key: str = "dev-integration-key"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
