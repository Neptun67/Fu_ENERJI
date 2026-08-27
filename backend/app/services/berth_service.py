from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.berth import Berth
from app.repositories.berth_repository import BerthRepository
from app.repositories.plan_repository import PlanRepository
from app.schemas.berth import BerthCreate, BerthUpdate

# Editing one of these invalidates a plan that used this berth; editing anything
# else (a name, say) does not. Length and depth are what the planner reads.
PLANNING_FIELDS = ("length_m", "depth_m")


class BerthService:
    """Berth business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = BerthRepository(db)
        self.plans = PlanRepository(db)

    def list_berths(self) -> list[Berth]:
        return self.repo.list_all()

    def get_berth(self, berth_id: int) -> Berth:
        berth = self.repo.get(berth_id)
        if berth is None:
            raise NotFoundError(f"Berth not found (id={berth_id})")
        return berth

    def create_berth(self, payload: BerthCreate) -> Berth:
        """Add a berth, flagging every existing plan as outdated.

        Unlike an edit or a deletion this touches all of them: each was solved for
        a quay that did not contain this berth, so none of them is still the answer
        to the current problem.
        """
        obj = Berth(**payload.model_dump())
        self.repo.add(obj)
        self.plans.mark_all_stale(f"Berth {obj.name!r} was added")
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_berth(self, berth_id: int, payload: BerthUpdate) -> Berth:
        """Apply a partial update, flagging plans if the change affects planning.

        A plan is a record of a moment, so it is not recalculated - but once the
        berth it was built from has moved on, the plan no longer describes the
        current quay and is marked stale so the reader knows.
        """
        obj = self.get_berth(berth_id)
        changes = payload.model_dump(exclude_unset=True)
        affects_planning = any(
            field in changes and getattr(obj, field) != changes[field]
            for field in PLANNING_FIELDS
        )
        for field, value in changes.items():
            setattr(obj, field, value)
        if affects_planning:
            self.plans.mark_stale_for_berth(obj.id, f"Berth {obj.name!r} was edited")
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_berth(self, berth_id: int) -> None:
        """Delete a berth, flagging any plan that used it as stale.

        Plans are never rewritten. One that referenced this berth keeps every row
        it was generated with - the name was copied at plan time - and is shown
        under "Outdated" so the record of what was decided outlives the data it
        was decided from.
        """
        obj = self.get_berth(berth_id)
        self.plans.mark_stale_for_berth(obj.id, f"Berth {obj.name!r} was deleted")
        self.repo.delete(obj)
        self.db.commit()
