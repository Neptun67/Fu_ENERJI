from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.plan import PlanGenerateRequest, PlanRead
from app.services.scheduling_service import SchedulingService

router = APIRouter(prefix="/plans", tags=["plans"])


def get_service(db: Session = Depends(get_db)) -> SchedulingService:
    return SchedulingService(db)


@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def generate_plan(
    payload: PlanGenerateRequest | None = Body(default=None),
    service: SchedulingService = Depends(get_service),
):
    """Generate and persist a new plan from the current ships and berths."""
    buffer_min = payload.buffer_min if payload else None
    return service.generate(buffer_min=buffer_min)


@router.get("", response_model=list[PlanRead])
def list_plans(service: SchedulingService = Depends(get_service)):
    """History of generated plans, newest first."""
    return service.list_plans()


@router.get("/{plan_id}", response_model=PlanRead)
def get_plan(plan_id: int, service: SchedulingService = Depends(get_service)):
    return service.get_plan(plan_id)
