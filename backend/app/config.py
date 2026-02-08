from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str = "Agentic QA Backend"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000"
    DATABASE_URL: str = ""
    REDIS_URL: str = ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()
