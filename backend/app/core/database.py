from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# pool_pre_ping: uykuya geçen (free-tier) DB bağlantılarını canlı tutar.
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: her istek için bir DB oturumu açıp kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
