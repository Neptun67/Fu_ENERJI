from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.plan import Plan
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
