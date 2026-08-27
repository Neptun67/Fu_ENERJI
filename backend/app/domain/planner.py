"""Berth planning core — pure, infrastructure-free, deterministic.

Approach (dispatch loop):
  1. Separate out ships that physically fit no berth at all (length/draft).
  2. For the rest, at each step find the next decision point (`now`): the earliest
     time at which any remaining ship could start.
  3. Among the ships that can start at that moment, pick one using a PRIORITY RULE
     (see `_priority_hrrn`) and place it on the least-wasteful feasible berth
     (best-fit).
  4. Mark that berth busy until end + manoeuvring buffer; repeat until none remain.

Why HRRN as the priority rule?
  Measured alternatives: FCFS (arrival order), SPT (shortest handling first), and
  SPT with aging. Plain SPT lowers total waiting but starves long ships (worst-case
  waiting degraded by up to 70%). HRRN keeps most of the gain while shrinking that
  cost, and has no constant to tune. Measurement table is in the README.

Not optimal; a reasonable, deterministic and explainable heuristic.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.types import (
    BerthInput,
    PlannedAssignment,
    PlanResult,
    ShipInput,
    UnassignedReason,
    UnassignedShip,
)


def _reason_for(ship: ShipInput, berths: list[BerthInput]) -> UnassignedReason:
    """Determine why a ship could not be assigned to any berth."""
    long_enough = any(b.length_m >= ship.length_m for b in berths)
    deep_enough = any(b.depth_m >= ship.draft_m for b in berths)
    if not long_enough and not deep_enough:
        return UnassignedReason.NO_SUITABLE_BERTH
    if not long_enough:
        return UnassignedReason.NO_SUITABLE_LENGTH
    if not deep_enough:
        return UnassignedReason.NO_SUITABLE_DEPTH
    # Each constraint is satisfied by some berth, but never both by the same one.
    return UnassignedReason.NO_SUITABLE_BERTH


def _priority_hrrn(ready: list[ShipInput], now: datetime) -> ShipInput:
    """Priority rule: HRRN (Highest Response Ratio Next).

    ratio = (waiting + handling) / handling

    Keeps SPT's advantage on total waiting, but a waiting ship's ratio grows over
    time, so it does not starve. Parameter-free: there is no constant to tune.
    Ties are broken by id to keep the plan deterministic.
    """
    def ratio(s: ShipInput) -> float:
        waiting = max(0.0, (now - s.eta).total_seconds() / 60)
        return (waiting + s.handling_time_min) / s.handling_time_min

    return max(ready, key=lambda s: (ratio(s), -s.id))


def plan(
    ships: list[ShipInput],
    berths: list[BerthInput],
    buffer_min: int,
) -> PlanResult:
    """Produce a berthing plan for the given ships, berths and manoeuvring buffer."""
    buffer = timedelta(minutes=buffer_min)

    # Per berth: the earliest moment the next ship may start.
    # None -> berth never used; the first ship starts at its ETA (no buffer).
    available_from: dict[int, datetime | None] = {b.id: None for b in berths}

    assignments: list[PlannedAssignment] = []
    unassigned: list[UnassignedShip] = []

    def feasible_for(ship: ShipInput) -> list[BerthInput]:
        return [
            b for b in berths
            if b.length_m >= ship.length_m and b.depth_m >= ship.draft_m
        ]

    # Ships that fit no berth are independent of ordering; separate them up front.
    remaining: list[ShipInput] = []
    for ship in sorted(ships, key=lambda s: s.id):
        if feasible_for(ship):
            remaining.append(ship)
        else:
            unassigned.append(UnassignedShip(ship.id, _reason_for(ship, berths)))

    # Dispatch loop: at each step choose among the ships that can start right now.
    while remaining:
        options: dict[int, tuple[datetime, BerthInput]] = {}
        for ship in remaining:
            def start_on(b: BerthInput, ship: ShipInput = ship) -> datetime:
                avail = available_from[b.id]
                return ship.eta if avail is None else max(ship.eta, avail)

            # On ties, prefer the least wasteful berth (best-fit).
            best = min(
                feasible_for(ship),
                key=lambda b: (start_on(b), b.length_m, b.depth_m, b.id),
            )
            options[ship.id] = (start_on(best), best)

        now = min(start for start, _ in options.values())
        ready = [s for s in remaining if options[s.id][0] == now]

        ship = _priority_hrrn(ready, now)
        start, berth = options[ship.id]
        end = start + timedelta(minutes=ship.handling_time_min)

        assignments.append(
            PlannedAssignment(
                ship_id=ship.id,
                berth_id=berth.id,
                eta=ship.eta,
                start_time=start,
                end_time=end,
            )
        )
        # The next ship on this berth may start no earlier than end + buffer.
        available_from[berth.id] = end + buffer
        remaining.remove(ship)

    return PlanResult(assignments=assignments, unassigned=unassigned, buffer_min=buffer_min)
