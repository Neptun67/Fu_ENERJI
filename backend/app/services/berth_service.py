from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.berth import Berth
from app.repositories.berth_repository import BerthRepository
from app.repositories.plan_repository import PlanRepository
from app.schemas.berth import BerthCreate, BerthUpdate


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
        berth = Berth(**payload.model_dump())
        self.repo.add(berth)
        self.db.commit()
        self.db.refresh(berth)
        return berth

    def update_berth(self, berth_id: int, payload: BerthUpdate) -> Berth:
        berth = self.get_berth(berth_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(berth, field, value)
        self.db.commit()
        self.db.refresh(berth)
        return berth

    def delete_berth(self, berth_id: int) -> None:
        """Delete a berth, flagging any plan that used it as stale.

        Plans are never rewritten. One that referenced this berth keeps every row
        it was generated with - the name was copied at plan time - and is shown
        under "Outdated" so the record of what was decided outlives the data it
        was decided from.
        """
        obj = self.get_berth(berth_id)
        self.plans.mark_stale_for_berth(obj.id, obj.name)
        self.repo.delete(obj)
        self.db.commit()
