from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.ship import Ship
from app.repositories.plan_repository import PlanRepository
from app.repositories.ship_repository import ShipRepository
from app.schemas.ship import ShipCreate, ShipUpdate

# Editing one of these invalidates a plan that used this ship; editing anything
# else (a name, say) does not. ETA, length, draft and handling time are what the planner reads.
PLANNING_FIELDS = ("eta", "length_m", "draft_m", "handling_time_min")


class ShipService:
    """Ship business logic: existence checks, transaction boundary, constraint errors."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ShipRepository(db)
        self.plans = PlanRepository(db)

    def list_ships(self) -> list[Ship]:
        return self.repo.list_all()

    def get_ship(self, ship_id: int) -> Ship:
        ship = self.repo.get(ship_id)
        if ship is None:
            raise NotFoundError(f"Ship not found (id={ship_id})")
        return ship

    def create_ship(self, payload: ShipCreate) -> Ship:
        """Add a ship, flagging every existing plan as outdated.

        Unlike an edit or a deletion this touches all of them: each was solved for
        a quay that did not contain this ship, so none of them is still the answer
        to the current problem.
        """
        obj = Ship(**payload.model_dump())
        self.repo.add(obj)
        self.plans.mark_all_stale(f"Ship {obj.name!r} was added")
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_ship(self, ship_id: int, payload: ShipUpdate) -> Ship:
        """Apply a partial update, flagging plans if the change affects planning.

        A plan is a record of a moment, so it is not recalculated - but once the
        ship it was built from has moved on, the plan no longer describes the
        current quay and is marked stale so the reader knows.
        """
        obj = self.get_ship(ship_id)
        changes = payload.model_dump(exclude_unset=True)
        affects_planning = any(
            field in changes and getattr(obj, field) != changes[field]
            for field in PLANNING_FIELDS
        )
        for field, value in changes.items():
            setattr(obj, field, value)
        if affects_planning:
            self.plans.mark_stale_for_ship(obj.id, f"Ship {obj.name!r} was edited")
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_ship(self, ship_id: int) -> None:
        """Delete a ship, flagging any plan that used it as stale.

        Plans are never rewritten. One that referenced this ship keeps every row
        it was generated with - the name was copied at plan time - and is shown
        under "Outdated" so the record of what was decided outlives the data it
        was decided from.
        """
        obj = self.get_ship(ship_id)
        self.plans.mark_stale_for_ship(obj.id, f"Ship {obj.name!r} was deleted")
        self.repo.delete(obj)
        self.db.commit()
