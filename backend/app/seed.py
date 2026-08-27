"""Demo verisi: tek komutla gerçekçi bir gemi/rıhtım seti yükler.

Çalıştırma:  python -m app.seed   (önce: alembic upgrade head)

Veri, planlamanın tüm ilginç durumlarını gösterecek şekilde tasarlandı:
- Aynı/yakın ETA'lı gemiler -> aynı rıhtımı paylaşır, tampon + bekleme görünür.
- Liman bilinçli olarak "monoton değil" (uzun-ama-sığ ve kısa-ama-derin rıhtımlar).
- Üç gemi bilinçli olarak atanamaz: uzunluk / derinlik / bileşik nedenlerle.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models import Berth, Plan, Ship


def _utc(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 1, hour, minute, tzinfo=timezone.utc)


# (ad, uzunluk_m, derinlik_m) — son ikisi limanı monoton olmaktan çıkarır
BERTHS: list[tuple[str, float, float]] = [
    ("Rıhtım 1", 300, 14),
    ("Rıhtım 2", 220, 11),
    ("Rıhtım 3", 180, 8),
    ("Rıhtım 4", 120, 6),
    ("Uzun İskele", 350, 7),    # çok uzun ama sığ
    ("Derin Dolfin", 100, 20),  # kısa ama çok derin
]

# (ad, eta, uzunluk_m, su_çekimi_m, elleçleme_dk)
SHIPS: list[tuple[str, datetime, float, float, int]] = [
    # --- atanabilir; bir kısmı R1/R2 için yarışır (bekleme + tampon görünür) ---
    ("MSC Aster", _utc(6, 0), 200, 10, 180),
    ("Nordic Star", _utc(6, 30), 160, 7, 120),
    ("Blue Horizon", _utc(7, 0), 280, 12, 240),   # yalnızca R1
    ("Aegean Trader", _utc(7, 15), 110, 5, 90),
    ("Marmara Pearl", _utc(7, 45), 210, 10, 150),
    ("Bosphorus", _utc(8, 15), 170, 8, 120),
    ("Levant Carrier", _utc(8, 45), 240, 11, 200),  # yalnızca R1
    ("Coastal Breeze", _utc(9, 0), 90, 4, 60),
    # --- bilinçli olarak atanamaz ---
    ("Titan Max", _utc(6, 45), 400, 10, 120),   # hiçbir rıhtım yeterince uzun değil
    ("Deep Diver", _utc(7, 30), 150, 21, 120),  # hiçbir rıhtım yeterince derin değil
    ("Odd Fit", _utc(8, 0), 300, 18, 150),      # uzunluk+derinlik birlikte karşılanamaz
]


def reset(session) -> None:
    # Planları önce sil: FK cascade ile atamalar/atanamayanlar da gider,
    # böylece gemi/rıhtımlar RESTRICT'e takılmadan silinebilir.
    session.execute(delete(Plan))
    session.execute(delete(Ship))
    session.execute(delete(Berth))
    session.commit()


def seed() -> None:
    with SessionLocal() as session:
        reset(session)
        session.add_all([Berth(name=n, length_m=l, depth_m=d) for n, l, d in BERTHS])
        session.add_all(
            [
                Ship(name=n, eta=e, length_m=l, draft_m=dr, handling_time_min=h)
                for n, e, l, dr, h in SHIPS
            ]
        )
        session.commit()
        print(f"Seed tamam: {len(BERTHS)} rıhtım, {len(SHIPS)} gemi eklendi.")


if __name__ == "__main__":
    seed()
