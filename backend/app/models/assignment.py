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
    """Bir geminin bir rıhtıma, belirli bir zaman aralığında atanması."""
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Plan silinince atamaları da silinir (cascade).
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    # ship/berth için ondelete belirtilmez -> RESTRICT: bir planda geçen gemi/rıhtım
    # silinemez; böylece geçmiş planların bütünlüğü korunur.
    ship_id: Mapped[int] = mapped_column(ForeignKey("ships.id"), nullable=False)
    berth_id: Mapped[int] = mapped_column(ForeignKey("berths.id"), nullable=False)
    # Planın üretildiği andaki ETA'nın kopyası. Bilinçli denormalizasyon: plan bir
    # ANLIK GÖRÜNTÜdür; gemi sonradan düzenlense de geçmiş planın beklemesi değişmemeli.
    eta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    plan: Mapped["Plan"] = relationship(back_populates="assignments")
    ship: Mapped["Ship"] = relationship(back_populates="assignments")
    berth: Mapped["Berth"] = relationship(back_populates="assignments")

    @property
    def waiting_min(self) -> int:
        """Bekleme süresi (dk). Kural domain'de tanımlıdır; burada yeniden yazılmaz.
        Canlı gemi kaydı değil, atamayla saklanan ETA kopyası kullanılır."""
        return waiting_minutes(self.start_time, self.eta)
