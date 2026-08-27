"""Yanaşma planlama çekirdeği — saf, altyapısız, deterministik.

Yaklaşım (dispatch / sevk döngüsü):
  1. Fiziksel olarak hiçbir rıhtıma sığmayan gemileri baştan ayır (uzunluk/derinlik).
  2. Kalanlar için, her adımda bir sonraki karar anını (`now`) bul: herhangi bir
     geminin başlayabileceği en erken zaman.
  3. O anda başlayabilecek gemiler arasından ÖNCELİK KURALI ile birini seç
     (bkz. `_priority_hrrn`), en az israf eden uygun rıhtıma (best-fit) yerleştir.
  4. Rıhtımı, bitiş + manevra tamponu kadar meşgul işaretle; kalan yoksa bitir.

Öncelik kuralı neden HRRN?
  Ölçtüğümüz alternatifler: FCFS (varış sırası), SPT (en kısa elleçleme önce),
  ve aging'li SPT varyantları. Düz SPT toplam beklemeyi azaltıyor ama uzun
  gemileri açlığa itiyor (en kötü bekleme %70'e kadar kötüleşti). HRRN,
  kazancın büyük kısmını korurken bu bedeli küçültüyor ve ayarlanacak bir
  sabit içermiyor. Ölçüm tablosu README'de.

Optimal değildir; makul, deterministik ve açıklanabilir bir sezgiseldir.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.types import (
    BerthInput,
    PlannedAssignment,
    PlanResult,
    ShipInput,
    UnassignedReason,
    UnassignedShip,
)


def _reason_for(ship: ShipInput, berths: list[BerthInput]) -> UnassignedReason:
    """Uygun rıhtım yokken atanamama nedenini belirler."""
    long_enough = any(b.length_m >= ship.length_m for b in berths)
    deep_enough = any(b.depth_m >= ship.draft_m for b in berths)
    if not long_enough and not deep_enough:
        return UnassignedReason.NO_SUITABLE_BERTH
    if not long_enough:
        return UnassignedReason.NO_SUITABLE_LENGTH
    if not deep_enough:
        return UnassignedReason.NO_SUITABLE_DEPTH
    # her iki kısıt tek tek karşılanıyor ama tek bir rıhtımda birlikte değil
    return UnassignedReason.NO_SUITABLE_BERTH


def _priority_hrrn(ready: list[ShipInput], now: datetime) -> ShipInput:
    """Öncelik kuralı: HRRN (Highest Response Ratio Next).

    oran = (bekleme + elleçleme) / elleçleme

    SPT'nin toplam beklemeyi azaltma avantajını korur, ama bekleyen gemi
    yaşlandıkça oranı büyüdüğü için açlığa (starvation) düşmez. Parametresizdir;
    ayarlanacak bir sabit yoktur. Eşitlikte id ile determinizm sağlanır.
    """
    def oran(s: ShipInput) -> float:
        bekleme = max(0.0, (now - s.eta).total_seconds() / 60)
        return (bekleme + s.handling_time_min) / s.handling_time_min

    return max(ready, key=lambda s: (oran(s), -s.id))


def plan(
    ships: list[ShipInput],
    berths: list[BerthInput],
    buffer_min: int,
) -> PlanResult:
    """Verilen gemi/rıhtım kümesi ve manevra tamponu için bir yanaşma planı üretir."""
    buffer = timedelta(minutes=buffer_min)

    # Her rıhtım için: bir sonraki geminin başlayabileceği en erken an.
    # None -> rıhtım hiç kullanılmadı, ilk gemi ETA'sında başlayabilir (tampon yok).
    available_from: dict[int, datetime | None] = {b.id: None for b in berths}

    assignments: list[PlannedAssignment] = []
    unassigned: list[UnassignedShip] = []

    def feasible_for(ship: ShipInput) -> list[BerthInput]:
        return [
            b for b in berths
            if b.length_m >= ship.length_m and b.depth_m >= ship.draft_m
        ]

    # Fiziksel olarak hiçbir rıhtıma sığmayanlar sıralamadan bağımsızdır; baştan ayrılır.
    remaining: list[ShipInput] = []
    for ship in sorted(ships, key=lambda s: s.id):
        if feasible_for(ship):
            remaining.append(ship)
        else:
            unassigned.append(UnassignedShip(ship.id, _reason_for(ship, berths)))

    # Dispatch döngüsü: her adımda "şu an başlayabilecek" gemiler arasından seçim yapılır.
    while remaining:
        options: dict[int, tuple[datetime, BerthInput]] = {}
        for ship in remaining:
            def start_on(b: BerthInput, ship: ShipInput = ship) -> datetime:
                avail = available_from[b.id]
                return ship.eta if avail is None else max(ship.eta, avail)

            # Eşitlikte en az israf eden rıhtım (best-fit).
            best = min(
                feasible_for(ship),
                key=lambda b: (start_on(b), b.length_m, b.depth_m, b.id),
            )
            options[ship.id] = (start_on(best), best)

        now = min(start for start, _ in options.values())
        ready = [s for s in remaining if options[s.id][0] == now]

        ship = _priority_hrrn(ready, now)
        start, berth = options[ship.id]
        end = start + timedelta(minutes=ship.handling_time_min)

        assignments.append(
            PlannedAssignment(
                ship_id=ship.id,
                berth_id=berth.id,
                eta=ship.eta,
                start_time=start,
                end_time=end,
            )
        )
        # Sonraki gemi bu rıhtımda en erken (bitiş + tampon) sonrası başlayabilir.
        available_from[berth.id] = end + buffer
        remaining.remove(ship)

    return PlanResult(assignments=assignments, unassigned=unassigned, buffer_min=buffer_min)
