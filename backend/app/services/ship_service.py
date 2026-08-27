from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.ship import Ship
from app.repositories.plan_repository import PlanRepository
from app.repositories.ship_repository import ShipRepository
from app.schemas.ship import ShipCreate, ShipUpdate


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
        ship = Ship(**payload.model_dump())
        self.repo.add(ship)
        self.db.commit()
        self.db.refresh(ship)
        return ship

    def update_ship(self, ship_id: int, payload: ShipUpdate) -> Ship:
        ship = self.get_ship(ship_id)
        # Apply only the fields that were sent (partial update).
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(ship, field, value)
        self.db.commit()
        self.db.refresh(ship)
        return ship

    def delete_ship(self, ship_id: int) -> None:
        """Delete a ship, flagging any plan that used it as stale.

        Plans are never rewritten. One that referenced this ship keeps every row
        it was generated with - the name was copied at plan time - and is shown
        under "Outdated" so the record of what was decided outlives the data it
        was decided from.
        """
        obj = self.get_ship(ship_id)
        self.plans.mark_stale_for_ship(obj.id, obj.name)
        self.repo.delete(obj)
        self.db.commit()
