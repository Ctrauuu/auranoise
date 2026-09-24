from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator, model_validator
from typing import Annotated

from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://auranoise:auranoise@localhost:5432/auranoise"
    jwt_secret: str = "development-only-change-me-at-once"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    initial_username: str = "admin"
    initial_password: str = "change-me-now"
    frontend_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("frontend_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def async_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql+asyncpg://", 1)
        parsed = urlsplit(value)
        query = [("ssl" if key == "sslmode" else key, item) for key, item in parse_qsl(parsed.query) if key != "channel_binding"]
        return urlunsplit(parsed._replace(query=urlencode(query)))

    @model_validator(mode="after")
    def production_secrets(self):
        if self.app_env == "production":
            if len(self.jwt_secret) < 32 or self.jwt_secret == "development-only-change-me-at-once":
                raise ValueError("JWT_SECRET must be a unique value of at least 32 characters in production")
            if self.initial_password == "change-me-now":
                raise ValueError("INITIAL_PASSWORD must be changed in production")
            if not self.frontend_origins or "*" in self.frontend_origins:
                raise ValueError("FRONTEND_ORIGINS must explicitly list allowed origins in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
