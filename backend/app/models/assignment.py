from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
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
    # SET NULL rather than RESTRICT: a ship or berth may be deleted while plans
    # still reference it. The row survives with its name copy, so the plan stays
    # readable; the plan itself is then marked stale (see Plan.stale_at).
    ship_id: Mapped[int | None] = mapped_column(
        ForeignKey("ships.id", ondelete="SET NULL"), nullable=True
    )
    berth_id: Mapped[int | None] = mapped_column(
        ForeignKey("berths.id", ondelete="SET NULL"), nullable=True
    )
    # Names at plan time. Denormalised on purpose: without them a deleted vessel
    # would leave a blank row in a plan that is meant to stay readable forever.
    ship_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    berth_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    # Copy of the ETA at plan time. Deliberate denormalisation: a plan is a
    # SNAPSHOT, so editing the ship later must not change a past plan.
    eta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    plan: Mapped["Plan"] = relationship(back_populates="assignments")
    ship: Mapped["Ship | None"] = relationship(back_populates="assignments")
    berth: Mapped["Berth | None"] = relationship(back_populates="assignments")

    @property
    def waiting_min(self) -> int:
        """Waiting time in minutes. The rule lives in the domain layer and is not
        re-implemented here. Uses the stored ETA copy, not the live ship record."""
        return waiting_minutes(self.start_time, self.eta)
