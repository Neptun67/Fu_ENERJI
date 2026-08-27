from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BerthBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    length_m: float = Field(..., gt=0, description="Metre")
    depth_m: float = Field(..., gt=0, description="Derinlik, metre")


class BerthCreate(BerthBase):
    pass


class BerthUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    length_m: float | None = Field(None, gt=0)
    depth_m: float | None = Field(None, gt=0)


class BerthRead(BerthBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
