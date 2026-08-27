from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Ortak CRUD veri erişimi. Transaction (commit) sınırını SERVICE yönetir;
    repository yalnızca oturum üzerinde okuma/yazma yapar."""

    model: type[ModelType]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: int) -> ModelType | None:
        return self.db.get(self.model, id_)

    def list_all(self) -> list[ModelType]:
        return list(self.db.scalars(select(self.model).order_by(self.model.id)))

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.flush()  # id ataması için; commit service'te.
        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
