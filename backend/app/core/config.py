from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama ayarları; değerler ortam değişkenlerinden (.env / platform) okunur."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB bağlantısı asla koda gömülmez.
    database_url: str = "postgresql+psycopg://port:port@localhost:5432/port_planning"

    # Manevra tamponu varsayılanı (dk). Gerekçe ROADMAP'te.
    buffer_min_default: int = 60

    # CORS: virgülle ayrılmış origin listesi (str tutulur; env'de JSON gerekmesin diye).
    # Prod'da örn: "https://uygulamam.vercel.app"
    cors_origins: str = "http://localhost:3000"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        # Railway/Heroku 'postgres://' verir; psycopg v3 sürücüsüne çeviririz.
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg://", 1)
            if v.startswith("postgresql://") and "+" not in v.split("://", 1)[0]:
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
