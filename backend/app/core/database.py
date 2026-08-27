from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# pool_pre_ping: uykuya geçen (free-tier) DB bağlantılarını canlı tutar.
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)

# SQLite'ta foreign key zorlaması varsayılan KAPALIDIR. Dev ortamında Postgres
# davranışını taklit edebilmek için (RESTRICT/CASCADE çalışsın diye) açıyoruz.
if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, _record):  # pragma: no cover
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: her istek için bir DB oturumu açıp kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
