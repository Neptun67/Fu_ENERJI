from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables (.env / platform)."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # The DB connection string is never hardcoded.
    database_url: str = "postgresql+psycopg://port:port@localhost:5432/port_planning"

    # Default manoeuvring buffer in minutes. Rationale in the README.
    buffer_min_default: int = 60

    # CORS: comma-separated origin list, kept as a str so the env var need not be
    # JSON. In production e.g. "https://myapp.vercel.app"
    cors_origins: str = "http://localhost:3000"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        # Railway and Heroku hand out 'postgres://'; map it to the psycopg v3 driver.
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg://", 1)
            if v.startswith("postgresql://") and "+" not in v.split("://", 1)[0]:
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        # URLs pasted from a hosting dashboard may carry a trailing '/'. Browsers send
        # the Origin header without one, so the match would silently fail. Normalise.
        origins = (o.strip().rstrip("/") for o in self.cors_origins.split(","))
        return [o for o in origins if o]


settings = Settings()
