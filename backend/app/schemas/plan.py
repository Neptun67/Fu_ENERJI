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
        """Human-readable reason text shown to the user."""
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
    """Plan generation request. If buffer_min is omitted, the configured default
    of 60 minutes is used."""
    # Upper bound 1440 min (24 h): the buffer represents one unberthing plus one
    # berthing manoeuvre. A value beyond a day is a data-entry error and would
    # silently produce a meaningless plan. See the ROADMAP change log.
    buffer_min: int | None = Field(
        None, gt=0, le=1440, description="Manoeuvring buffer in minutes, 1-1440"
    )
