from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Iterable

from .models import DutyEvent, DutyStatus, DutyTotals, EventType, HOSConfiguration


def duty_status_for(event_type: EventType) -> DutyStatus:
    if event_type is EventType.DRIVING:
        return DutyStatus.DRIVING
    if event_type in {EventType.PICKUP, EventType.DROPOFF, EventType.FUEL}:
        return DutyStatus.ON_DUTY_NOT_DRIVING
    return DutyStatus.OFF_DUTY


def is_qualifying_non_driving_interruption(
    event: DutyEvent, config: HOSConfiguration
) -> bool:
    return (
        event.duty_status is not DutyStatus.DRIVING
        and event.duration_minutes >= config.qualifying_break_minutes
    )


def daily_duty_totals(events: Iterable[DutyEvent]) -> dict[date, DutyTotals]:
    """Split events at local midnight and return totals for touched calendar days."""

    buckets: dict[date, dict[DutyStatus, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for event in events:
        cursor = event.start
        while cursor < event.end:
            next_day = cursor.date() + timedelta(days=1)
            midnight = datetime.combine(next_day, time.min, tzinfo=cursor.tzinfo)
            portion_end = min(event.end, midnight)
            buckets[cursor.date()][event.duty_status] += (
                portion_end - cursor
            ).total_seconds() / 60
            cursor = portion_end

    return {
        day: DutyTotals(
            driving_minutes=totals[DutyStatus.DRIVING],
            on_duty_not_driving_minutes=totals[DutyStatus.ON_DUTY_NOT_DRIVING],
            off_duty_minutes=totals[DutyStatus.OFF_DUTY],
            sleeper_berth_minutes=totals[DutyStatus.SLEEPER_BERTH],
        )
        for day, totals in buckets.items()
    }
