from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.unassigned_entry import UnassignedEntry


class Plan(Base):
    """Persisted record of a generated berthing plan, for retrospective review."""
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Buffer value at plan time (parameter snapshot).
    buffer_min: Mapped[int] = mapped_column(Integer, nullable=False)
    # Objective metric: total waiting across assigned ships, in minutes.
    total_waiting_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    unassigned_entries: Mapped[list["UnassignedEntry"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
