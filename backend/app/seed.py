"""Demo data: loads a realistic set of ships and berths in one command.

Run with:  python -m app.seed              (light day, the default)
           python -m app.seed --busy       (congested day)

Two scenarios are provided because the choice of scheduling rule only shows up
under capacity pressure. On the light day the berths absorb every arrival and
almost nothing waits; on the busy day ships queue, the manoeuvring buffer starts
to cost real berth time, and the timeline shows what the planner is actually
optimising. Both share the same quay and the same three unassignable ships.

The data is designed to exercise every interesting case of the planner:
- Ships with equal or close ETAs compete for the same berth, so the buffer and
  the resulting waiting time are visible.
- The port is deliberately non-uniform (a long-but-shallow and a short-but-deep
  berth), so best-fit selection matters.
- Three ships are deliberately unassignable: by length, by draft, and by the two
  constraints not being satisfiable by a single berth.
"""
from __future__ import annotations

import argparse
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

ShipRow = tuple[str, datetime, float, float, int]

# --- deliberately unassignable; present in both scenarios ---------------------
UNASSIGNABLE: list[ShipRow] = [
    ("Titan Max", _utc(6, 45), 400, 10, 120),   # no berth is long enough
    ("Deep Diver", _utc(7, 30), 150, 21, 120),  # no berth is deep enough
    ("Odd Fit", _utc(8, 0), 300, 18, 150),      # length and depth not met together
]

# --- light day: berths mostly keep up, a little queuing on berths 1 and 2 -----
LIGHT: list[ShipRow] = [
    ("MSC Aster", _utc(6, 0), 200, 10, 180),
    ("Nordic Star", _utc(6, 30), 160, 7, 120),
    ("Blue Horizon", _utc(7, 0), 280, 12, 240),   # fits berth 1 only
    ("Aegean Trader", _utc(7, 15), 110, 5, 90),
    ("Marmara Pearl", _utc(7, 45), 210, 10, 150),
    ("Bosphorus", _utc(8, 15), 170, 8, 120),
    ("Levant Carrier", _utc(8, 45), 240, 11, 200),  # fits berth 1 only
    ("Coastal Breeze", _utc(9, 0), 90, 4, 60),
]

# --- busy day: the light day plus a second wave, running into the evening -----
# Sized so the quay runs at roughly 85-90% utilisation: queues form, but the
# port does not gridlock. Includes long-but-shallow and short-but-deep vessels
# so Long Pier and Deep Dolphin are actually used rather than sitting idle.
BUSY_EXTRA: list[ShipRow] = [
    ("Anatolia Express", _utc(9, 30), 190, 9, 150),
    ("Cape Meridian", _utc(9, 45), 320, 6, 180),    # long and shallow -> Long Pier
    ("Iskenderun", _utc(10, 15), 150, 7, 120),
    ("Black Sea Trader", _utc(10, 30), 230, 10, 200),
    ("Pelagos", _utc(11, 0), 95, 16, 90),           # short and deep -> Deep Dolphin
    ("Adriatic Dawn", _utc(11, 30), 260, 12, 210),  # fits berth 1 only
    ("Gulf Runner", _utc(12, 0), 130, 6, 100),
    ("Ionian Spirit", _utc(12, 45), 175, 8, 140),
    ("Aegean Falcon", _utc(13, 30), 205, 10, 160),
    ("Cilicia", _utc(14, 0), 340, 6, 200),          # long and shallow -> Long Pier
    ("Sea Lynx", _utc(14, 45), 100, 5, 80),
    ("Bosphorus Queen", _utc(15, 30), 215, 11, 190),
    ("Northern Light", _utc(16, 15), 165, 8, 130),
    ("Taurus", _utc(17, 0), 285, 13, 220),          # fits berth 1 only
    ("Halic", _utc(17, 45), 98, 18, 110),           # short and deep -> Deep Dolphin
    ("Levantine Star", _utc(18, 30), 180, 9, 150),
]


def scenario_ships(busy: bool) -> list[ShipRow]:
    return [*LIGHT, *BUSY_EXTRA, *UNASSIGNABLE] if busy else [*LIGHT, *UNASSIGNABLE]


def reset(session) -> None:
    # Delete plans first: the FK cascade removes assignments and unassigned entries,
    # so ships and berths can then be deleted without hitting RESTRICT.
    session.execute(delete(Plan))
    session.execute(delete(Ship))
    session.execute(delete(Berth))
    session.commit()


def seed(busy: bool = False) -> None:
    ships = scenario_ships(busy)
    with SessionLocal() as session:
        reset(session)
        session.add_all([Berth(name=n, length_m=length, depth_m=d) for n, length, d in BERTHS])
        session.add_all(
            [
                Ship(name=n, eta=e, length_m=length, draft_m=dr, handling_time_min=h)
                for n, e, length, dr, h in ships
            ]
        )
        session.commit()
        label = "busy day" if busy else "light day"
        print(f"Seed complete ({label}): {len(BERTHS)} berths and {len(ships)} ships inserted.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--busy",
        action="store_true",
        help="load the congested scenario instead of the light one",
    )
    seed(busy=parser.parse_args().busy)
