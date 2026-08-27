from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Enum tek kaynaktan gelir: saf domain katmanı. Böylece model ve planlayıcı
# aynı 'atanamama nedeni' tanımını paylaşır.
from app.domain.types import UnassignedReason
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.plan import Plan
    from app.models.ship import Ship

__all__ = ["UnassignedEntry", "UnassignedReason"]


class UnassignedEntry(Base):
    """Bir planda atanamayan gemi + nedeni."""
    __tablename__ = "unassigned_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    ship_id: Mapped[int] = mapped_column(ForeignKey("ships.id"), nullable=False)
    reason: Mapped[UnassignedReason] = mapped_column(
        SAEnum(UnassignedReason, name="unassigned_reason"), nullable=False
    )

    plan: Mapped["Plan"] = relationship(back_populates="unassigned_entries")
    ship: Mapped["Ship"] = relationship()
