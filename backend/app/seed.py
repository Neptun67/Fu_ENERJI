"""Demo data: loads a realistic set of ships and berths in one command.

Run with:  python -m app.seed   (after: alembic upgrade head)

The data is designed to exercise every interesting case of the planner:
- Ships with equal or close ETAs compete for the same berth, so the buffer and
  the resulting waiting time are visible.
- The port is deliberately non-uniform (a long-but-shallow and a short-but-deep
  berth), so best-fit selection matters.
- Three ships are deliberately unassignable: by length, by draft, and by the two
  constraints not being satisfiable by a single berth.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models import Berth, Plan, Ship


def _utc(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 1, hour, minute, tzinfo=timezone.utc)


# (name, length_m, depth_m) - the last two make the port non-uniform
BERTHS: list[tuple[str, float, float]] = [
    ("Berth 1", 300, 14),
    ("Berth 2", 220, 11),
    ("Berth 3", 180, 8),
    ("Berth 4", 120, 6),
    ("Long Pier", 350, 7),      # very long but shallow
    ("Deep Dolphin", 100, 20),  # short but very deep
]

# (name, eta, length_m, draft_m, handling_time_min)
SHIPS: list[tuple[str, datetime, float, float, int]] = [
    # --- assignable; some compete for berths 1 and 2, showing waiting + buffer ---
    ("MSC Aster", _utc(6, 0), 200, 10, 180),
    ("Nordic Star", _utc(6, 30), 160, 7, 120),
    ("Blue Horizon", _utc(7, 0), 280, 12, 240),   # fits berth 1 only
    ("Aegean Trader", _utc(7, 15), 110, 5, 90),
    ("Marmara Pearl", _utc(7, 45), 210, 10, 150),
    ("Bosphorus", _utc(8, 15), 170, 8, 120),
    ("Levant Carrier", _utc(8, 45), 240, 11, 200),  # fits berth 1 only
    ("Coastal Breeze", _utc(9, 0), 90, 4, 60),
    # --- deliberately unassignable ---
    ("Titan Max", _utc(6, 45), 400, 10, 120),   # no berth is long enough
    ("Deep Diver", _utc(7, 30), 150, 21, 120),  # no berth is deep enough
    ("Odd Fit", _utc(8, 0), 300, 18, 150),      # length and depth not met together
]


def reset(session) -> None:
    # Delete plans first: the FK cascade removes assignments and unassigned entries,
    # so ships and berths can then be deleted without hitting RESTRICT.
    session.execute(delete(Plan))
    session.execute(delete(Ship))
    session.execute(delete(Berth))
    session.commit()


def seed() -> None:
    with SessionLocal() as session:
        reset(session)
        session.add_all([Berth(name=n, length_m=length, depth_m=d) for n, length, d in BERTHS])
        session.add_all(
            [
                Ship(name=n, eta=e, length_m=length, draft_m=dr, handling_time_min=h)
                for n, e, length, dr, h in SHIPS
            ]
        )
        session.commit()
        print(f"Seed complete: {len(BERTHS)} berths and {len(SHIPS)} ships inserted.")


if __name__ == "__main__":
    seed()
