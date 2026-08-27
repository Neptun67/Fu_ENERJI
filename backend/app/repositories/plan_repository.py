from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.plan import Plan
from app.models.unassigned_entry import UnassignedEntry
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    model = Plan

    def _detail_options(self):
        # Eager-load the relations needed for serialisation to avoid N+1 queries.
        return (
            selectinload(Plan.assignments).selectinload(Assignment.ship),
            selectinload(Plan.unassigned_entries),
        )

    def get_with_details(self, id_: int) -> Plan | None:
        stmt = select(Plan).where(Plan.id == id_).options(*self._detail_options())
        return self.db.scalars(stmt).unique().one_or_none()

    def list_with_details(self) -> list[Plan]:
        stmt = select(Plan).order_by(Plan.id.desc()).options(*self._detail_options())
        return list(self.db.scalars(stmt).unique())

    def _mark_stale(self, condition, reason: str) -> int:
        """Flag matching plans as stale. Already-stale plans keep their first reason,
        because the earliest cause is the one that explains the record."""
        stmt = select(Plan).where(condition, Plan.stale_at.is_(None))
        plans = list(self.db.scalars(stmt).unique())
        now = datetime.now(timezone.utc)
        for plan in plans:
            plan.stale_at = now
            plan.stale_reason = reason
        return len(plans)

    def mark_stale_for_ship(self, ship_id: int, ship_name: str) -> int:
        return self._mark_stale(
            or_(
                Plan.assignments.any(Assignment.ship_id == ship_id),
                Plan.unassigned_entries.any(UnassignedEntry.ship_id == ship_id),
            ),
            f"Ship {ship_name!r} was deleted",
        )

    def mark_stale_for_berth(self, berth_id: int, berth_name: str) -> int:
        return self._mark_stale(
            Plan.assignments.any(Assignment.berth_id == berth_id),
            f"Berth {berth_name!r} was deleted",
        )
