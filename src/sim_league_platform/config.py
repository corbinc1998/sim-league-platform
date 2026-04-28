"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    postgres_user: str = Field(...)
    postgres_password: str = Field(...)
    postgres_db: str = Field(...)
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)

    mongo_user: str = Field(...)
    mongo_password: str = Field(...)
    mongo_db: str = Field(...)
    mongo_host: str = Field(default="localhost")
    mongo_port: int = Field(default=27017)

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_url_sync(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
