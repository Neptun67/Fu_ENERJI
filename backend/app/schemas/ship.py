from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShipBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    eta: datetime
    length_m: float = Field(..., gt=0, description="Metre")
    draft_m: float = Field(..., gt=0, description="Draft in metres")
    handling_time_min: int = Field(..., gt=0, description="Handling time in minutes")


class ShipCreate(ShipBase):
    pass


class ShipUpdate(BaseModel):
    """Partial update: every field is optional."""
    name: str | None = Field(None, min_length=1, max_length=120)
    eta: datetime | None = None
    length_m: float | None = Field(None, gt=0)
    draft_m: float | None = Field(None, gt=0)
    handling_time_min: int | None = Field(None, gt=0)


class ShipRead(ShipBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
