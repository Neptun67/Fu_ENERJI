"""Yanaşma planlama çekirdeği — saf, altyapısız, deterministik.

Yaklaşım (greedy / açgözlü sezgisel):
  1. Gemileri varış zamanına (ETA) göre sırala.
  2. Her gemi için fiziksel olarak uygun (uzunluk + derinlik) rıhtımları bul.
  3. Bu rıhtımlar arasından gemiyi EN ERKEN başlatabileni seç.
     Eşitlikte en az israf eden rıhtımı seç (best-fit): küçük gemiyi küçük
     rıhtıma koyup büyük rıhtımları büyük gemilere sakla.
  4. Uygun hiç rıhtım yoksa gemiyi nedeniyle birlikte 'atanamayan'a ekle.

Optimal değildir; her geminin başlangıcını yerel olarak en aza indirir. Bu,
toplam bekleme için makul ve açıklaması kolay bir çözümdür.
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

    # ETA'ya göre sırala; eşitlikte kısa elleçleme önce (rıhtım çabuk boşalır), sonra id.
    ordered = sorted(ships, key=lambda s: (s.eta, s.handling_time_min, s.id))

    for ship in ordered:
        feasible = [
            b for b in berths
            if b.length_m >= ship.length_m and b.depth_m >= ship.draft_m
        ]
        if not feasible:
            unassigned.append(UnassignedShip(ship.id, _reason_for(ship, berths)))
            continue

        # Her uygun rıhtım için olası başlangıcı hesapla; en erken başlatanı (best-fit ile) seç.
        def start_on(b: BerthInput) -> datetime:
            avail = available_from[b.id]
            return ship.eta if avail is None else max(ship.eta, avail)

        chosen = min(
            feasible,
            key=lambda b: (start_on(b), b.length_m, b.depth_m, b.id),
        )
        start = start_on(chosen)
        end = start + timedelta(minutes=ship.handling_time_min)

        assignments.append(
            PlannedAssignment(
                ship_id=ship.id,
                berth_id=chosen.id,
                eta=ship.eta,
                start_time=start,
                end_time=end,
            )
        )
        # Sonraki gemi bu rıhtımda en erken (bitiş + tampon) sonrası başlayabilir.
        available_from[chosen.id] = end + buffer

    return PlanResult(assignments=assignments, unassigned=unassigned, buffer_min=buffer_min)
