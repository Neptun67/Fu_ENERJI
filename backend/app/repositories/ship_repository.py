from app.models.ship import Ship
from app.repositories.base import BaseRepository


class ShipRepository(BaseRepository[Ship]):
    model = Ship
