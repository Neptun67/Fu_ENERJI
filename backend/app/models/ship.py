from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.assignment import Assignment


class Ship(Base, TimestampMixin):
    __tablename__ = "ships"
    __table_args__ = (
        CheckConstraint("length_m > 0", name="ck_ship_length_positive"),
        CheckConstraint("draft_m > 0", name="ck_ship_draft_positive"),
        CheckConstraint("handling_time_min > 0", name="ck_ship_handling_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    eta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False)
    draft_m: Mapped[float] = mapped_column(Float, nullable=False)
    handling_time_min: Mapped[int] = mapped_column(Integer, nullable=False)

    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="ship",
        # The database sets the reference to NULL on delete; let it, rather
        # than loading every assignment just to null it row by row.
        passive_deletes=True,
    )
