from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.unassigned_entry import UnassignedReason


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ship_id: int
    berth_id: int
    start_time: datetime
    end_time: datetime
    waiting_min: int  # Assignment.waiting_min property'sinden okunur.


class UnassignedEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ship_id: int
    reason: UnassignedReason

    @computed_field  # type: ignore[misc]
    @property
    def reason_message(self) -> str:
        """Kullanıcıya gösterilecek, insan-okunur neden metni."""
        return self.reason.message


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    buffer_min: int
    total_waiting_min: int
    assignments: list[AssignmentRead] = []
    unassigned_entries: list[UnassignedEntryRead] = []


class PlanGenerateRequest(BaseModel):
    """Plan üretim isteği. buffer_min verilmezse ayarlardaki varsayılan (60 dk) kullanılır."""
    buffer_min: int | None = Field(None, gt=0, description="Manevra tamponu (dk)")
