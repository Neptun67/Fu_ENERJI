from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.types import waiting_minutes
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.berth import Berth
    from app.models.plan import Plan
    from app.models.ship import Ship


class Assignment(Base):
    """A ship assigned to a berth over a specific time window."""
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Deleting a plan cascades to its assignments.
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    # No ondelete on ship/berth -> RESTRICT: a ship or berth referenced by a plan
    # cannot be deleted, which keeps historical plans intact.
    ship_id: Mapped[int] = mapped_column(ForeignKey("ships.id"), nullable=False)
    berth_id: Mapped[int] = mapped_column(ForeignKey("berths.id"), nullable=False)
    # Copy of the ETA at plan time. Deliberate denormalisation: a plan is a
    # SNAPSHOT, so editing the ship later must not change a past plan.
    eta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    plan: Mapped["Plan"] = relationship(back_populates="assignments")
    ship: Mapped["Ship"] = relationship(back_populates="assignments")
    berth: Mapped["Berth"] = relationship(back_populates="assignments")

    @property
    def waiting_min(self) -> int:
        """Waiting time in minutes. The rule lives in the domain layer and is not
        re-implemented here. Uses the stored ETA copy, not the live ship record."""
        return waiting_minutes(self.start_time, self.eta)
