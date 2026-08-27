from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.assignment import Assignment


class Berth(Base, TimestampMixin):
    __tablename__ = "berths"
    __table_args__ = (
        CheckConstraint("length_m > 0", name="ck_berth_length_positive"),
        CheckConstraint("depth_m > 0", name="ck_berth_depth_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False)
    depth_m: Mapped[float] = mapped_column(Float, nullable=False)

    assignments: Mapped[list["Assignment"]] = relationship(back_populates="berth")
