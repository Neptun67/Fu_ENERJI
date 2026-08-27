from app.models.berth import Berth
from app.repositories.base import BaseRepository


class BerthRepository(BaseRepository[Berth]):
    model = Berth
