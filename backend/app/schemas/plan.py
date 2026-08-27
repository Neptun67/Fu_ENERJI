from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.unassigned_entry import UnassignedReason


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    # Nullable: the vessel or berth may have been deleted since the plan was made.
    ship_id: int | None
    berth_id: int | None
    # Names as they were at plan time, so the row stays readable either way.
    ship_name: str
    berth_name: str
    start_time: datetime
    end_time: datetime
    waiting_min: int  # read from the Assignment.waiting_min property


class UnassignedEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ship_id: int | None
    ship_name: str
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
    # Set when a ship or berth the plan used was deleted. The plan is kept exactly
    # as generated; this only tells the reader it no longer matches current data.
    stale_at: datetime | None = None
    stale_reason: str | None = None
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
