"""Pure domain types. Depend on the standard library only — they know nothing
about SQLAlchemy, FastAPI or any other infrastructure. This keeps the planning
core deterministic and easy to test."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime


class UnassignedReason(str, enum.Enum):
    """Physical reasons a ship could not be assigned to a berth."""
    NO_SUITABLE_LENGTH = "no_suitable_length"
    NO_SUITABLE_DEPTH = "no_suitable_depth"
    NO_SUITABLE_BERTH = "no_suitable_berth"  # length and depth not met together

    @property
    def message(self) -> str:
        return {
            UnassignedReason.NO_SUITABLE_LENGTH: "No berth is long enough",
            UnassignedReason.NO_SUITABLE_DEPTH: "No berth is deep enough",
            UnassignedReason.NO_SUITABLE_BERTH: (
                "No single berth satisfies both length and depth"
            ),
        }[self]


@dataclass(frozen=True)
class ShipInput:
    id: int
    eta: datetime
    length_m: float
    draft_m: float
    handling_time_min: int


@dataclass(frozen=True)
class BerthInput:
    id: int
    length_m: float
    depth_m: float


def waiting_minutes(start_time: datetime, eta: datetime) -> int:
    """Waiting time in minutes = start - ETA. Clamped at zero.

    This is the SINGLE source of the rule; the ORM model calls this function so the
    rule is never re-implemented in the infrastructure layer.
    """
    return max(0, int((start_time - eta).total_seconds() // 60))


@dataclass(frozen=True)
class PlannedAssignment:
    ship_id: int
    berth_id: int
    eta: datetime          # ETA at plan time; stored alongside the assignment
    start_time: datetime
    end_time: datetime

    @property
    def waiting_min(self) -> int:
        return waiting_minutes(self.start_time, self.eta)


@dataclass(frozen=True)
class UnassignedShip:
    ship_id: int
    reason: UnassignedReason


@dataclass(frozen=True)
class PlanResult:
    assignments: list[PlannedAssignment] = field(default_factory=list)
    unassigned: list[UnassignedShip] = field(default_factory=list)
    buffer_min: int = 0

    @property
    def total_waiting_min(self) -> int:
        """Objective metric: total waiting across all assigned ships (minutes)."""
        return sum(a.waiting_min for a in self.assignments)
