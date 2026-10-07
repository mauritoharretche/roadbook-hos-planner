from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.trips.domain.hos import (
    EventType,
    HOSConfiguration,
    HOSPlanner,
    RouteSegment,
    StopAction,
)
from apps.trips.domain.hos.models import PlanErrorCode
from apps.trips.domain.hos.rules import daily_duty_totals


DEPARTURE = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)


def route(hours: float, miles: float | None = None, *, stop_after=None, name="route"):
    return RouteSegment(
        name=name,
        distance_miles=hours * 50 if miles is None else miles,
        driving_minutes=hours * 60,
        stop_after=stop_after,
    )


def plan(segments, cycle=0, departure=DEPARTURE, config=None):
    return HOSPlanner(config).plan(
        segments,
        current_cycle_used_hours=cycle,
        departure_at=departure,
    )


def event_types(result):
    return [event.event_type for event in result.events]


def test_short_trip_has_only_driving_and_no_break_or_rest():
    result = plan([route(2)])

    assert result.feasible
    assert event_types(result) == [EventType.DRIVING]
    assert result.total_driving_minutes == 120
    assert result.total_on_duty_minutes == 120
    assert result.total_off_duty_minutes == 0


def test_exactly_eight_driving_hours_needs_no_break_without_more_driving():
    result = plan([route(8)])

    assert result.feasible
    assert EventType.BREAK_30_MIN not in event_types(result)


def test_driving_beyond_eight_hours_inserts_30_minute_break():
    result = plan([route(8 + 1 / 60)])

    assert result.feasible
    assert event_types(result) == [
        EventType.DRIVING,
        EventType.BREAK_30_MIN,
        EventType.DRIVING,
    ]
    assert result.events[1].duration_minutes == 30


def test_pickup_satisfies_required_30_minute_interruption():
    result = plan(
        [
            route(8, stop_after=StopAction.PICKUP, name="to pickup"),
            route(1 / 60, name="after pickup"),
        ]
    )

    assert result.feasible
    assert event_types(result) == [
        EventType.DRIVING,
        EventType.PICKUP,
        EventType.DRIVING,
    ]
    assert EventType.BREAK_30_MIN not in event_types(result)


def test_dropoff_satisfies_required_30_minute_interruption():
    result = plan(
        [
            route(8, stop_after=StopAction.DROPOFF, name="to dropoff"),
            route(1 / 60, name="after dropoff"),
        ]
    )

    assert result.feasible
    assert event_types(result) == [
        EventType.DRIVING,
        EventType.DROPOFF,
        EventType.DRIVING,
    ]
    assert EventType.BREAK_30_MIN not in event_types(result)


def test_exactly_eleven_driving_hours_needs_no_daily_rest_without_more_driving():
    result = plan([route(11)])

    assert result.feasible
    assert EventType.REST_10_HOURS not in event_types(result)


def test_driving_beyond_eleven_hours_inserts_ten_hour_rest():
    result = plan([route(11 + 1 / 60)])

    assert result.feasible
    assert EventType.REST_10_HOURS in event_types(result)
    rest_index = event_types(result).index(EventType.REST_10_HOURS)
    assert result.events[rest_index].duration_minutes == 600


def test_exactly_fourteen_elapsed_window_hours_needs_no_rest_without_more_driving():
    # 10 driving hours + four 30-minute fuel stops + pickup + dropoff = 14 hours.
    result = plan(
        [
            route(10, miles=4000, stop_after=StopAction.PICKUP),
            RouteSegment("dropoff", 0, 0, StopAction.DROPOFF),
        ]
    )

    assert result.feasible
    assert result.total_elapsed_minutes == 14 * 60
    assert EventType.REST_10_HOURS not in event_types(result)


def test_driving_beyond_fourteen_elapsed_window_hours_inserts_ten_hour_rest():
    result = plan(
        [
            route(10, miles=4000, stop_after=StopAction.PICKUP),
            RouteSegment("dropoff", 0, 0, StopAction.DROPOFF),
            route(1 / 60, name="after window"),
        ]
    )

    assert result.feasible
    assert EventType.REST_10_HOURS in event_types(result)


def test_trip_crossing_midnight_has_consistent_daily_totals():
    result = plan([route(5)], departure=datetime(2026, 1, 5, 20, 0, tzinfo=timezone.utc))
    totals = daily_duty_totals(result.events)

    assert len(totals) == 2
    assert sum(day.total_minutes for day in totals.values()) == result.total_elapsed_minutes
    assert sum(day.driving_minutes for day in totals.values()) == result.total_driving_minutes


def test_long_trip_requires_multiple_ten_hour_rests():
    result = plan([route(23, miles=230)])

    assert result.feasible
    assert event_types(result).count(EventType.REST_10_HOURS) == 2


def test_fuel_stop_at_exactly_one_thousand_miles():
    result = plan([route(5, miles=1000)])

    assert event_types(result).count(EventType.FUEL) == 1
    assert result.events[-1].event_type is EventType.FUEL


def test_no_fuel_stop_just_below_one_thousand_miles():
    result = plan([route(5, miles=999.99)])

    assert EventType.FUEL not in event_types(result)


def test_fuel_stops_repeat_beyond_one_thousand_miles():
    result = plan([route(5, miles=2001)])

    assert event_types(result).count(EventType.FUEL) == 2


def test_fuel_stop_satisfies_the_30_minute_break_when_due_at_eight_hours():
    # 1,000 miles occurs at minute 480, followed by one additional driving minute.
    result = plan([route(8 + 1 / 60, miles=1000 * 481 / 480)])

    assert event_types(result).count(EventType.FUEL) == 1
    assert EventType.BREAK_30_MIN not in event_types(result)


def test_current_cycle_near_seventy_can_finish_when_capacity_remains():
    result = plan([route(0.5)], cycle=69)

    assert result.feasible
    assert result.cycle_hours_used == 69.5
    assert result.cycle_hours_remaining == 0.5


def test_current_cycle_exactly_seventy_makes_further_driving_infeasible():
    result = plan([route(1 / 60)], cycle=70)

    assert not result.feasible
    assert result.error_code is PlanErrorCode.CYCLE_CAPACITY_EXHAUSTED
    assert result.events == ()


def test_cycle_capacity_exhausted_during_pickup_is_infeasible_without_overflow():
    result = plan([RouteSegment("pickup", 0, 0, StopAction.PICKUP)], cycle=69.5)

    assert not result.feasible
    assert result.error_code is PlanErrorCode.CYCLE_CAPACITY_EXHAUSTED
    assert result.cycle_hours_used == 69.5
    assert result.events == ()


def test_cycle_capacity_exhausted_during_dropoff_is_infeasible_without_overflow():
    result = plan([route(0.5, stop_after=StopAction.DROPOFF)], cycle=69)

    assert not result.feasible
    assert result.error_code is PlanErrorCode.CYCLE_CAPACITY_EXHAUSTED
    assert result.cycle_hours_used == 69.5
    assert event_types(result) == [EventType.DRIVING]


def test_infeasible_trip_stops_at_cycle_boundary_without_violation():
    result = plan([route(2)], cycle=69.5)

    assert not result.feasible
    assert result.completed_distance_miles == 25
    assert result.cycle_hours_used == 70
    assert result.cycle_hours_remaining == 0


def test_events_are_chronological_contiguous_and_do_not_overlap():
    result = plan([route(12, miles=1200, stop_after=StopAction.PICKUP), route(1)])

    assert result.feasible
    for previous, current in zip(result.events, result.events[1:]):
        assert previous.end == current.start
        assert previous.end <= current.start


def test_daily_time_totals_remain_internally_consistent():
    result = plan(
        [route(13, miles=1300, stop_after=StopAction.PICKUP)],
        departure=datetime(2026, 1, 5, 18, 0, tzinfo=timezone.utc),
    )
    totals = daily_duty_totals(result.events)

    assert sum(day.total_minutes for day in totals.values()) == pytest.approx(
        result.total_elapsed_minutes
    )
    assert sum(day.driving_minutes for day in totals.values()) == pytest.approx(
        result.total_driving_minutes
    )
    assert sum(day.on_duty_not_driving_minutes for day in totals.values()) == pytest.approx(
        result.total_on_duty_minutes - result.total_driving_minutes
    )
    assert sum(day.off_duty_minutes for day in totals.values()) == pytest.approx(
        result.total_off_duty_minutes
    )


def test_invalid_cycle_usage_over_seventy_is_rejected():
    with pytest.raises(ValueError, match="cannot exceed"):
        plan([route(1)], cycle=70.01)
