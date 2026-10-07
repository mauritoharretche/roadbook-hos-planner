from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from math import isfinite
from typing import Optional

from .exceptions import HOSValidationError


class DutyStatus(str, Enum):
    OFF_DUTY = "OFF_DUTY"
    SLEEPER_BERTH = "SLEEPER_BERTH"
    DRIVING = "DRIVING"
    ON_DUTY_NOT_DRIVING = "ON_DUTY_NOT_DRIVING"


class EventType(str, Enum):
    DRIVING = "DRIVING"
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"
    FUEL = "FUEL"
    BREAK_30_MIN = "BREAK_30_MIN"
    REST_10_HOURS = "REST_10_HOURS"


class StopAction(str, Enum):
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"


class PlanErrorCode(str, Enum):
    CYCLE_CAPACITY_EXHAUSTED = "CYCLE_CAPACITY_EXHAUSTED"


@dataclass(frozen=True)
class HOSConfiguration:
    """Assessment HOS rules. Fuel duration is a documented planning assumption."""

    max_driving_minutes: float = 11 * 60
    max_duty_window_minutes: float = 14 * 60
    break_after_driving_minutes: float = 8 * 60
    qualifying_break_minutes: float = 30
    daily_reset_minutes: float = 10 * 60
    max_cycle_on_duty_minutes: float = 70 * 60
    pickup_minutes: float = 60
    dropoff_minutes: float = 60
    fuel_interval_miles: float = 1000
    fuel_minutes: float = 30

    def __post_init__(self) -> None:
        numeric_fields = (
            "max_driving_minutes",
            "max_duty_window_minutes",
            "break_after_driving_minutes",
            "qualifying_break_minutes",
            "daily_reset_minutes",
            "max_cycle_on_duty_minutes",
            "pickup_minutes",
            "dropoff_minutes",
            "fuel_interval_miles",
            "fuel_minutes",
        )
        for field_name in numeric_fields:
            value = getattr(self, field_name)
            if not isfinite(value) or value <= 0:
                raise HOSValidationError(f"{field_name} must be a positive finite number")


@dataclass(frozen=True)
class RouteSegment:
    """A fixed route fixture portion; service occurs after its driving portion."""

    name: str
    distance_miles: float
    driving_minutes: float
    stop_after: Optional[StopAction] = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise HOSValidationError("Route segment name is required")
        if not isfinite(self.distance_miles) or self.distance_miles < 0:
            raise HOSValidationError("distance_miles must be a finite non-negative number")
        if not isfinite(self.driving_minutes) or self.driving_minutes < 0:
            raise HOSValidationError("driving_minutes must be a finite non-negative number")
        if (self.distance_miles == 0) != (self.driving_minutes == 0):
            raise HOSValidationError(
                "distance_miles and driving_minutes must both be zero or both be positive"
            )


@dataclass(frozen=True)
class DutyEvent:
    event_type: EventType
    duty_status: DutyStatus
    start: datetime
    end: datetime
    route_progress_miles: float
    reason: str
    segment_index: Optional[int] = None
    segment_name: Optional[str] = None

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise HOSValidationError("Duty event cannot end before it starts")
        if not isfinite(self.route_progress_miles) or self.route_progress_miles < 0:
            raise HOSValidationError("route_progress_miles must be finite and non-negative")

    @property
    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60


@dataclass(frozen=True)
class DutyTotals:
    driving_minutes: float = 0
    on_duty_not_driving_minutes: float = 0
    off_duty_minutes: float = 0
    sleeper_berth_minutes: float = 0

    @property
    def total_minutes(self) -> float:
        return (
            self.driving_minutes
            + self.on_duty_not_driving_minutes
            + self.off_duty_minutes
            + self.sleeper_berth_minutes
        )


@dataclass(frozen=True)
class PlanResult:
    feasible: bool
    events: tuple[DutyEvent, ...]
    total_distance_miles: float
    completed_distance_miles: float
    total_driving_minutes: float
    total_on_duty_minutes: float
    total_off_duty_minutes: float
    cycle_hours_used: float
    cycle_hours_remaining: float
    warnings: tuple[str, ...] = field(default_factory=tuple)
    error_code: Optional[PlanErrorCode] = None

    @property
    def total_elapsed_minutes(self) -> float:
        return sum(event.duration_minutes for event in self.events)
