from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.berth import Berth
from app.repositories.berth_repository import BerthRepository
from app.schemas.berth import BerthCreate, BerthUpdate


class BerthService:
    """Rıhtım iş mantığı."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = BerthRepository(db)

    def list_berths(self) -> list[Berth]:
        return self.repo.list_all()

    def get_berth(self, berth_id: int) -> Berth:
        berth = self.repo.get(berth_id)
        if berth is None:
            raise NotFoundError(f"Rıhtım bulunamadı (id={berth_id})")
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
        berth = self.get_berth(berth_id)
        self.repo.delete(berth)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Bu rıhtım bir planda kullanıldığı için silinemez")
