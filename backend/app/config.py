from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Aqlabs Object Store Command Center API", alias="APP_NAME")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    database_url: str = Field(
        default="sqlite:///./s3mock.db",
        alias="DATABASE_URL",
    )
    storage_root: str = Field(default="/data/storage", alias="STORAGE_ROOT")
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ALLOWED_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
