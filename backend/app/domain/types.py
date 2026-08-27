"""Saf domain tipleri. Yalnızca standart kütüphaneye bağlıdır;
SQLAlchemy / FastAPI gibi altyapıyı bilmez. Böylece planlama çekirdeği
deterministik ve kolay test edilebilir kalır."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime


class UnassignedReason(str, enum.Enum):
    """Bir geminin neden atanamadığını belirten fiziksel nedenler."""
    NO_SUITABLE_LENGTH = "no_suitable_length"
    NO_SUITABLE_DEPTH = "no_suitable_depth"
    NO_SUITABLE_BERTH = "no_suitable_berth"  # uzunluk+derinlik birlikte karşılanamıyor

    @property
    def message(self) -> str:
        return {
            UnassignedReason.NO_SUITABLE_LENGTH: "Uygun uzunlukta rıhtım yok",
            UnassignedReason.NO_SUITABLE_DEPTH: "Yeterli derinlikte rıhtım yok",
            UnassignedReason.NO_SUITABLE_BERTH: (
                "Uzunluk ve derinliği birlikte karşılayan rıhtım yok"
            ),
        }[self]


@dataclass(frozen=True)
class ShipInput:
    id: int
    eta: datetime
    length_m: float
    draft_m: float
    handling_time_min: int


@dataclass(frozen=True)
class BerthInput:
    id: int
    length_m: float
    depth_m: float


def waiting_minutes(start_time: datetime, eta: datetime) -> int:
    """Bekleme (dk) = başlangıç - ETA. Negatifse 0'a kırpılır.

    Bu kuralın TEK kaynağı burasıdır; ORM modeli de bunu çağırır, böylece
    aynı iş kuralı altyapı katmanında yeniden yazılmaz.
    """
    return max(0, int((start_time - eta).total_seconds() // 60))


@dataclass(frozen=True)
class PlannedAssignment:
    ship_id: int
    berth_id: int
    eta: datetime          # planın üretildiği andaki ETA; atamayla birlikte saklanır
    start_time: datetime
    end_time: datetime

    @property
    def waiting_min(self) -> int:
        return waiting_minutes(self.start_time, self.eta)


@dataclass(frozen=True)
class UnassignedShip:
    ship_id: int
    reason: UnassignedReason


@dataclass(frozen=True)
class PlanResult:
    assignments: list[PlannedAssignment] = field(default_factory=list)
    unassigned: list[UnassignedShip] = field(default_factory=list)
    buffer_min: int = 0

    @property
    def total_waiting_min(self) -> int:
        """Hedef metrik: atanan tüm gemilerin toplam beklemesi (dk)."""
        return sum(a.waiting_min for a in self.assignments)
