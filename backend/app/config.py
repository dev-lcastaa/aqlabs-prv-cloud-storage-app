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
    storage_roots: str | None = Field(default=None, alias="STORAGE_ROOTS")
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ALLOWED_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def storage_roots_list(self) -> list[str]:
        """Return the list of storage roots. Prefer STORAGE_ROOTS if provided, otherwise fall back to STORAGE_ROOT."""
        if self.storage_roots:
            return [p.strip() for p in self.storage_roots.split(",") if p.strip()]
        return [self.storage_root]


@lru_cache
def get_settings() -> Settings:
    return Settings()
