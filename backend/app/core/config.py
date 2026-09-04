from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "FinanFlow"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "dev-only-change-me"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8
    DATABASE_URL: str = "postgresql+psycopg://finanflow:finanflow@localhost:5432/finanflow"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8080"
    TZ: str = "America/Sao_Paulo"
    MAX_UPLOAD_BYTES: int = 2 * 1024 * 1024
    MAX_CSV_ROWS: int = 5000

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
