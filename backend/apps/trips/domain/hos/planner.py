from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite
from typing import Iterable

from .exceptions import HOSValidationError
from .models import (
    DutyEvent,
    EventType,
    HOSConfiguration,
    PlanErrorCode,
    PlanResult,
    RouteSegment,
    StopAction,
)
from .rules import duty_status_for

EPSILON = 1e-7
NO_ROLLOVER_WARNING = (
    "Cycle availability is calculated from the supplied aggregate hours only; "
    "no 8-day rollover or restart is assumed."
)


@dataclass
class _PlanningState:
    current_time: datetime
    route_progress_miles: float
    distance_since_fuel_miles: float
    driving_in_window_minutes: float
    elapsed_in_window_minutes: float
    driving_since_break_minutes: float
    cycle_on_duty_minutes: float


class HOSPlanner:
    """Creates a contiguous, deterministic HOS timeline from fixed route segments."""

    def __init__(self, config: HOSConfiguration | None = None) -> None:
        self.config = config or HOSConfiguration()

    def plan(
        self,
        route_segments: Iterable[RouteSegment],
        *,
        current_cycle_used_hours: float,
        departure_at: datetime,
    ) -> PlanResult:
        segments = tuple(route_segments)
        self._validate_inputs(segments, current_cycle_used_hours, departure_at)
        state = _PlanningState(
            current_time=departure_at,
            route_progress_miles=0,
            distance_since_fuel_miles=0,
            driving_in_window_minutes=0,
            elapsed_in_window_minutes=0,
            driving_since_break_minutes=0,
            cycle_on_duty_minutes=current_cycle_used_hours * 60,
        )
        events: list[DutyEvent] = []
        total_distance = sum(segment.distance_miles for segment in segments)

        for segment_index, segment in enumerate(segments):
            remaining_minutes = segment.driving_minutes
            remaining_miles = segment.distance_miles

            while remaining_minutes > EPSILON:
                if state.driving_in_window_minutes >= self.config.max_driving_minutes - EPSILON:
                    self._add_rest(events, state)
                    continue
                if state.elapsed_in_window_minutes >= self.config.max_duty_window_minutes - EPSILON:
                    self._add_rest(events, state)
                    continue
                if state.driving_since_break_minutes >= self.config.break_after_driving_minutes - EPSILON:
                    self._add_break(events, state, segment_index, segment.name)
                    continue
                if state.cycle_on_duty_minutes >= self.config.max_cycle_on_duty_minutes - EPSILON:
                    return self._infeasible(events, state, total_distance)

                drive_minutes = self._next_driving_boundary(
                    state, remaining_minutes, remaining_miles
                )
                if drive_minutes <= EPSILON:
                    raise RuntimeError("Planner made no progress while scheduling driving")

                miles_per_minute = remaining_miles / remaining_minutes
                drive_miles = miles_per_minute * drive_minutes
                self._append_event(
                    events,
                    state,
                    event_type=EventType.DRIVING,
                    duration_minutes=drive_minutes,
                    reason="Route driving",
                    segment_index=segment_index,
                    segment_name=segment.name,
                )
                state.route_progress_miles += drive_miles
                state.distance_since_fuel_miles += drive_miles
                state.driving_in_window_minutes += drive_minutes
                state.elapsed_in_window_minutes += drive_minutes
                state.driving_since_break_minutes += drive_minutes
                state.cycle_on_duty_minutes += drive_minutes
                remaining_minutes -= drive_minutes
                remaining_miles -= drive_miles

                if state.distance_since_fuel_miles >= self.config.fuel_interval_miles - EPSILON:
                    if not self._has_cycle_capacity(state, self.config.fuel_minutes):
                        return self._infeasible(events, state, total_distance)
                    self._add_fuel(events, state, segment_index, segment.name)

            if segment.stop_after is not None:
                event_type, duration, reason = self._service_for(segment.stop_after)
                if not self._has_cycle_capacity(state, duration):
                    return self._infeasible(events, state, total_distance)
                self._append_event(
                    events,
                    state,
                    event_type=event_type,
                    duration_minutes=duration,
                    reason=reason,
                    segment_index=segment_index,
                    segment_name=segment.name,
                )
                state.elapsed_in_window_minutes += duration
                state.cycle_on_duty_minutes += duration
                if duration >= self.config.qualifying_break_minutes:
                    state.driving_since_break_minutes = 0

        return self._result(feasible=True, events=events, state=state, total_distance=total_distance)

    def _validate_inputs(
        self,
        segments: tuple[RouteSegment, ...],
        current_cycle_used_hours: float,
        departure_at: datetime,
    ) -> None:
        if departure_at.tzinfo is None or departure_at.utcoffset() is None:
            raise HOSValidationError("departure_at must be timezone-aware")
        if not isfinite(current_cycle_used_hours) or current_cycle_used_hours < 0:
            raise HOSValidationError(
                "current_cycle_used_hours must be a finite non-negative number"
            )
        if current_cycle_used_hours > self.config.max_cycle_on_duty_minutes / 60:
            raise HOSValidationError("current_cycle_used_hours cannot exceed the 70-hour cycle")
        if not segments:
            raise HOSValidationError("At least one route segment is required")

    def _next_driving_boundary(
        self,
        state: _PlanningState,
        remaining_minutes: float,
        remaining_miles: float,
    ) -> float:
        candidates = [
            remaining_minutes,
            self.config.max_driving_minutes - state.driving_in_window_minutes,
            self.config.max_duty_window_minutes - state.elapsed_in_window_minutes,
            self.config.break_after_driving_minutes - state.driving_since_break_minutes,
            self.config.max_cycle_on_duty_minutes - state.cycle_on_duty_minutes,
        ]
        if remaining_miles > EPSILON:
            miles_to_fuel = self.config.fuel_interval_miles - state.distance_since_fuel_miles
            candidates.append(remaining_minutes * miles_to_fuel / remaining_miles)
        return min(candidates)

    def _add_break(
        self,
        events: list[DutyEvent],
        state: _PlanningState,
        segment_index: int,
        segment_name: str,
    ) -> None:
        self._append_event(
            events,
            state,
            event_type=EventType.BREAK_30_MIN,
            duration_minutes=self.config.qualifying_break_minutes,
            reason="Required 30-minute non-driving interruption after 8 cumulative driving hours",
            segment_index=segment_index,
            segment_name=segment_name,
        )
        state.elapsed_in_window_minutes += self.config.qualifying_break_minutes
        state.driving_since_break_minutes = 0

    def _add_rest(self, events: list[DutyEvent], state: _PlanningState) -> None:
        self._append_event(
            events,
            state,
            event_type=EventType.REST_10_HOURS,
            duration_minutes=self.config.daily_reset_minutes,
            reason="Required 10 consecutive hours off duty to reset daily driving limits",
        )
        state.driving_in_window_minutes = 0
        state.elapsed_in_window_minutes = 0
        state.driving_since_break_minutes = 0

    def _add_fuel(
        self,
        events: list[DutyEvent],
        state: _PlanningState,
        segment_index: int,
        segment_name: str,
    ) -> None:
        self._append_event(
            events,
            state,
            event_type=EventType.FUEL,
            duration_minutes=self.config.fuel_minutes,
            reason="Planned fuel stop at the 1,000-mile interval (assessment assumption: 30 minutes)",
            segment_index=segment_index,
            segment_name=segment_name,
        )
        state.elapsed_in_window_minutes += self.config.fuel_minutes
        state.cycle_on_duty_minutes += self.config.fuel_minutes
        state.driving_since_break_minutes = 0
        state.distance_since_fuel_miles = 0

    def _service_for(self, action: StopAction) -> tuple[EventType, float, str]:
        if action is StopAction.PICKUP:
            return EventType.PICKUP, self.config.pickup_minutes, "Required pickup service"
        return EventType.DROPOFF, self.config.dropoff_minutes, "Required dropoff service"

    def _append_event(
        self,
        events: list[DutyEvent],
        state: _PlanningState,
        *,
        event_type: EventType,
        duration_minutes: float,
        reason: str,
        segment_index: int | None = None,
        segment_name: str | None = None,
    ) -> None:
        start = state.current_time
        end = start + timedelta(minutes=duration_minutes)
        events.append(
            DutyEvent(
                event_type=event_type,
                duty_status=duty_status_for(event_type),
                start=start,
                end=end,
                route_progress_miles=state.route_progress_miles,
                reason=reason,
                segment_index=segment_index,
                segment_name=segment_name,
            )
        )
        state.current_time = end

    def _has_cycle_capacity(self, state: _PlanningState, duration: float) -> bool:
        return (
            state.cycle_on_duty_minutes + duration
            <= self.config.max_cycle_on_duty_minutes + EPSILON
        )

    def _infeasible(
        self, events: list[DutyEvent], state: _PlanningState, total_distance: float
    ) -> PlanResult:
        return self._result(
            feasible=False,
            events=events,
            state=state,
            total_distance=total_distance,
            error_code=PlanErrorCode.CYCLE_CAPACITY_EXHAUSTED,
            extra_warning="The trip cannot finish without exceeding the available 70-hour cycle capacity.",
        )

    def _result(
        self,
        *,
        feasible: bool,
        events: list[DutyEvent],
        state: _PlanningState,
        total_distance: float,
        error_code: PlanErrorCode | None = None,
        extra_warning: str | None = None,
    ) -> PlanResult:
        total_driving = sum(
            event.duration_minutes
            for event in events
            if event.event_type is EventType.DRIVING
        )
        total_on_duty = sum(
            event.duration_minutes
            for event in events
            if event.duty_status.value in {"DRIVING", "ON_DUTY_NOT_DRIVING"}
        )
        total_off_duty = sum(
            event.duration_minutes
            for event in events
            if event.duty_status.value == "OFF_DUTY"
        )
        warnings = [NO_ROLLOVER_WARNING]
        if extra_warning:
            warnings.append(extra_warning)
        return PlanResult(
            feasible=feasible,
            events=tuple(events),
            total_distance_miles=total_distance,
            completed_distance_miles=state.route_progress_miles,
            total_driving_minutes=total_driving,
            total_on_duty_minutes=total_on_duty,
            total_off_duty_minutes=total_off_duty,
            cycle_hours_used=state.cycle_on_duty_minutes / 60,
            cycle_hours_remaining=max(
                0, (self.config.max_cycle_on_duty_minutes - state.cycle_on_duty_minutes) / 60
            ),
            warnings=tuple(warnings),
            error_code=error_code,
        )
