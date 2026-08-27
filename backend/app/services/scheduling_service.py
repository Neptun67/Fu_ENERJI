from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.domain.planner import plan as run_planner
from app.domain.types import BerthInput, ShipInput
from app.models.assignment import Assignment
from app.models.plan import Plan
from app.models.unassigned_entry import UnassignedEntry
from app.repositories.berth_repository import BerthRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.ship_repository import ShipRepository


class SchedulingService:
    """Connects the pure planner to the database: loads data, maps it to domain
    inputs, calls plan(), and persists the result as a Plan."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.ships = ShipRepository(db)
        self.berths = BerthRepository(db)
        self.plans = PlanRepository(db)

    def generate(self, buffer_min: int | None = None) -> Plan:
        buffer = buffer_min if buffer_min is not None else settings.buffer_min_default

        # 1) DB -> domain inputs
        ship_inputs = [
            ShipInput(
                id=s.id, eta=s.eta, length_m=s.length_m,
                draft_m=s.draft_m, handling_time_min=s.handling_time_min,
            )
            for s in self.ships.list_all()
        ]
        berth_inputs = [
            BerthInput(id=b.id, length_m=b.length_m, depth_m=b.depth_m)
            for b in self.berths.list_all()
        ]

        # 2) Pure core
        result = run_planner(ship_inputs, berth_inputs, buffer)

        # 3) Domain result -> persisted Plan
        plan_row = Plan(buffer_min=buffer, total_waiting_min=result.total_waiting_min)
        plan_row.assignments = [
            Assignment(
                ship_id=a.ship_id, berth_id=a.berth_id, eta=a.eta,
                start_time=a.start_time, end_time=a.end_time,
            )
            for a in result.assignments
        ]
        plan_row.unassigned_entries = [
            UnassignedEntry(ship_id=u.ship_id, reason=u.reason)
            for u in result.unassigned
        ]
        self.db.add(plan_row)
        self.db.commit()

        # Return with relations eager-loaded for serialisation.
        return self.plans.get_with_details(plan_row.id)

    def list_plans(self) -> list[Plan]:
        return self.plans.list_with_details()

    def get_plan(self, plan_id: int) -> Plan:
        plan_row = self.plans.get_with_details(plan_id)
        if plan_row is None:
            raise NotFoundError(f"Plan not found (id={plan_id})")
        return plan_row
