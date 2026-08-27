from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ship import ShipCreate, ShipRead, ShipUpdate
from app.services.ship_service import ShipService

router = APIRouter(prefix="/ships", tags=["ships"])


def get_service(db: Session = Depends(get_db)) -> ShipService:
    return ShipService(db)


@router.get("", response_model=list[ShipRead])
def list_ships(service: ShipService = Depends(get_service)):
    return service.list_ships()


@router.post("", response_model=ShipRead, status_code=status.HTTP_201_CREATED)
def create_ship(payload: ShipCreate, service: ShipService = Depends(get_service)):
    return service.create_ship(payload)


@router.get("/{ship_id}", response_model=ShipRead)
def get_ship(ship_id: int, service: ShipService = Depends(get_service)):
    return service.get_ship(ship_id)


@router.patch("/{ship_id}", response_model=ShipRead)
def update_ship(ship_id: int, payload: ShipUpdate, service: ShipService = Depends(get_service)):
    return service.update_ship(ship_id, payload)


@router.delete("/{ship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ship(ship_id: int, service: ShipService = Depends(get_service)):
    service.delete_ship(ship_id)
