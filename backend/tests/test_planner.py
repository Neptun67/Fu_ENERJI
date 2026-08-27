"""Unit tests for the planner core: pure, database-free, deterministic."""
from datetime import datetime, timedelta, timezone

from app.domain.planner import plan
from app.domain.types import BerthInput, ShipInput, UnassignedReason, waiting_minutes

T0 = datetime(2026, 8, 26, 8, 0, tzinfo=timezone.utc)


def ship(id_, eta=T0, length=150, draft=8, handling=120):
    return ShipInput(id=id_, eta=eta, length_m=length, draft_m=draft, handling_time_min=handling)


def berth(id_, length=300, depth=15):
    return BerthInput(id=id_, length_m=length, depth_m=depth)


def test_single_ship_assigned_at_eta():
    res = plan([ship(1)], [berth(1)], buffer_min=60)
    assert len(res.assignments) == 1
    a = res.assignments[0]
    assert a.berth_id == 1
    assert a.start_time == T0            # first ship starts at its ETA, no buffer
    assert a.waiting_min == 0
    assert res.unassigned == []


def test_end_time_uses_handling_time():
    res = plan([ship(1, handling=240)], [berth(1)], buffer_min=60)
    assert res.assignments[0].end_time == T0 + timedelta(minutes=240)


def test_too_long_is_unassigned_length():
    res = plan([ship(1, length=400)], [berth(1, length=300, depth=15)], buffer_min=60)
    assert res.assignments == []
    assert res.unassigned[0].reason == UnassignedReason.NO_SUITABLE_LENGTH


def test_too_deep_is_unassigned_depth():
    res = plan([ship(1, draft=20)], [berth(1, length=300, depth=15)], buffer_min=60)
    assert res.unassigned[0].reason == UnassignedReason.NO_SUITABLE_DEPTH


def test_combined_infeasible_is_no_suitable_berth():
    # A long-but-shallow and a short-but-deep berth exist; neither alone fits the ship.
    s = ship(1, length=250, draft=12)
    berths = [berth(1, length=300, depth=6), berth(2, length=100, depth=20)]
    res = plan([s], berths, buffer_min=60)
    assert res.unassigned[0].reason == UnassignedReason.NO_SUITABLE_BERTH


def test_two_ships_same_berth_buffer_applied():
    # Same ETA, one berth: the second ship waits for the first plus the buffer.
    res = plan([ship(1, handling=120), ship(2, handling=120)], [berth(1)], buffer_min=60)
    a1, a2 = sorted(res.assignments, key=lambda a: a.start_time)
    gap = a2.start_time - a1.end_time
    assert gap == timedelta(minutes=60)          # buffer applied exactly
    assert a2.waiting_min == 180                 # 120 handling + 60 buffer


def test_two_ships_two_berths_run_in_parallel():
    res = plan([ship(1), ship(2)], [berth(1), berth(2)], buffer_min=60)
    assert len(res.assignments) == 2
    assert {a.berth_id for a in res.assignments} == {1, 2}   # different berths
    assert all(a.start_time == T0 for a in res.assignments)  # ikisi de beklemeden
    assert res.total_waiting_min == 0


def test_ship_cannot_start_before_its_eta():
    # A ship that has not arrived cannot be pulled forward, even on an idle berth (rule 4).
    late = ship(1, eta=T0 + timedelta(hours=1))       # 09:00
    early = ship(2, eta=T0)                           # 08:00
    res = plan([late, early], [berth(1)], buffer_min=60)
    by_time = sorted(res.assignments, key=lambda a: a.start_time)
    assert by_time[0].ship_id == 2                    # only the arrived ship may start
    assert by_time[1].ship_id == 1
    assert all(a.start_time >= a.eta for a in res.assignments)


def test_hrrn_rescues_a_long_ship_from_starvation():
    """Why HRRN exists: a long ship is not pushed to the back under a stream of
    short arrivals.

    Setup: the long ship (600 min) arrives at T0 but carries the HIGHEST id, so it
    loses the tie at the first decision point. A short ship (60 min) then arrives
    every 90 minutes. Plain SPT would keep picking the fresh short ship and leave
    the long one until last. Under HRRN the long ship's waiting/handling ratio
    grows, so at the next decision point it outranks the fresh arrivals.

    Note: HRRN bounds starvation, it does not eliminate it. Short ships that have
    waited the same time grow their ratio faster and can still go first.
    """
    LONG = 99
    shorts = [ship(i, eta=T0 + timedelta(minutes=90 * (i - 1)), handling=60)
              for i in range(1, 8)]
    long_ship = ship(LONG, eta=T0, handling=600)
    res = plan([*shorts, long_ship], [berth(1)], buffer_min=30)

    order = [a.ship_id for a in sorted(res.assignments, key=lambda a: a.start_time)]
    long_waiting = next(a.waiting_min for a in res.assignments if a.ship_id == LONG)

    assert order[-1] != LONG, f"long ship pushed to the back: {order}"
    # Plain SPT makes it wait 630 min here; HRRN must stay well below that.
    assert long_waiting < 300, f"long ship starved: {long_waiting} min"


def test_total_waiting_is_sum():
    res = plan([ship(1, handling=120), ship(2, handling=120), ship(3, handling=120)],
               [berth(1)], buffer_min=30)
    # 1: 0 bekler; 2: 120+30=150; 3: (150+120)+30=300 -> toplam 450
    assert res.total_waiting_min == sum(a.waiting_min for a in res.assignments)
    assert res.total_waiting_min == 0 + 150 + 300


def test_deterministic():
    args = ([ship(1), ship(2), ship(3)], [berth(1), berth(2)], 45)
    r1 = plan(*args)
    r2 = plan(*args)
    assert [(a.ship_id, a.berth_id, a.start_time) for a in r1.assignments] == \
           [(a.ship_id, a.berth_id, a.start_time) for a in r2.assignments]


def test_no_berths_all_unassigned():
    res = plan([ship(1), ship(2)], [], buffer_min=60)
    assert len(res.unassigned) == 2
    assert all(u.reason == UnassignedReason.NO_SUITABLE_BERTH for u in res.unassigned)


def test_waiting_minutes_is_clamped_at_zero():
    # The rule has one source (waiting_minutes); a start before ETA never goes negative.
    assert waiting_minutes(T0 + timedelta(minutes=90), T0) == 90
    assert waiting_minutes(T0, T0) == 0
    assert waiting_minutes(T0 - timedelta(minutes=30), T0) == 0
