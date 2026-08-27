from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.ship import Ship
from app.repositories.ship_repository import ShipRepository
from app.schemas.ship import ShipCreate, ShipUpdate


class ShipService:
    """Gemi iş mantığı: varlık kontrolü, transaction sınırı, kısıt hataları."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ShipRepository(db)

    def list_ships(self) -> list[Ship]:
        return self.repo.list_all()

    def get_ship(self, ship_id: int) -> Ship:
        ship = self.repo.get(ship_id)
        if ship is None:
            raise NotFoundError(f"Gemi bulunamadı (id={ship_id})")
        return ship

    def create_ship(self, payload: ShipCreate) -> Ship:
        ship = Ship(**payload.model_dump())
        self.repo.add(ship)
        self.db.commit()
        self.db.refresh(ship)
        return ship

    def update_ship(self, ship_id: int, payload: ShipUpdate) -> Ship:
        ship = self.get_ship(ship_id)
        # Yalnızca gönderilen alanları uygula (kısmi güncelleme).
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(ship, field, value)
        self.db.commit()
        self.db.refresh(ship)
        return ship

    def delete_ship(self, ship_id: int) -> None:
        ship = self.get_ship(ship_id)
        self.repo.delete(ship)
        try:
            self.db.commit()
        except IntegrityError:
            # FK RESTRICT: gemi bir planda geçiyorsa silinemez.
            self.db.rollback()
            raise ConflictError("Bu gemi bir planda kullanıldığı için silinemez") from None
