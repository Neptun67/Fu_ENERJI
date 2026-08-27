from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

# The enum has a single source: the pure domain layer. Model and planner therefore
# share one definition of why a ship was not assigned.
from app.domain.types import UnassignedReason
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.plan import Plan
    from app.models.ship import Ship

__all__ = ["UnassignedEntry", "UnassignedReason"]


class UnassignedEntry(Base):
    """A ship that could not be assigned in a plan, with its reason."""
    __tablename__ = "unassigned_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    ship_id: Mapped[int | None] = mapped_column(
        ForeignKey("ships.id", ondelete="SET NULL"), nullable=True
    )
    ship_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    reason: Mapped[UnassignedReason] = mapped_column(
        SAEnum(UnassignedReason, name="unassigned_reason"), nullable=False
    )

    plan: Mapped["Plan"] = relationship(back_populates="unassigned_entries")
    ship: Mapped["Ship | None"] = relationship()
