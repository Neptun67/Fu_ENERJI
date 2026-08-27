from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.berth import BerthCreate, BerthRead, BerthUpdate
from app.services.berth_service import BerthService

router = APIRouter(prefix="/berths", tags=["berths"])


def get_service(db: Session = Depends(get_db)) -> BerthService:
    return BerthService(db)


@router.get("", response_model=list[BerthRead])
def list_berths(service: BerthService = Depends(get_service)):
    return service.list_berths()


@router.post("", response_model=BerthRead, status_code=status.HTTP_201_CREATED)
def create_berth(payload: BerthCreate, service: BerthService = Depends(get_service)):
    return service.create_berth(payload)


@router.get("/{berth_id}", response_model=BerthRead)
def get_berth(berth_id: int, service: BerthService = Depends(get_service)):
    return service.get_berth(berth_id)


@router.patch("/{berth_id}", response_model=BerthRead)
def update_berth(berth_id: int, payload: BerthUpdate, service: BerthService = Depends(get_service)):
    return service.update_berth(berth_id, payload)


@router.delete("/{berth_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_berth(berth_id: int, service: BerthService = Depends(get_service)):
    service.delete_berth(berth_id)
