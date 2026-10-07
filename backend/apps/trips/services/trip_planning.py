from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from apps.trips.domain.hos import HOSPlanner, RouteSegment, StopAction
from apps.trips.domain.hos.models import DutyEvent, PlanResult
from apps.trips.domain.hos.rules import daily_duty_totals
from apps.trips.routing import MockRoutingProvider, Route, RoutingProvider


@dataclass
class TripPlanningService:
    """Coordinates routing data with the framework-independent HOS planner."""

    routing_provider: RoutingProvider
    planner: HOSPlanner

    @classmethod
    def with_mock_routing(cls) -> "TripPlanningService":
        return cls(routing_provider=MockRoutingProvider(), planner=HOSPlanner())

    def geocode(self, query: str) -> dict:
        location = self.routing_provider.geocode(query)
        return {
            "query": query,
            "label": location.label,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }

    def plan_trip(
        self,
        *,
        current_location: str,
        pickup_location: str,
        dropoff_location: str,
        current_cycle_used_hours: float,
        departure_at: datetime,
    ) -> dict:
        locations = [
            self.routing_provider.geocode(current_location),
            self.routing_provider.geocode(pickup_location),
            self.routing_provider.geocode(dropoff_location),
        ]
        route = self.routing_provider.calculate_route(locations)
        plan_result = self.planner.plan(
            self._to_domain_segments(route),
            current_cycle_used_hours=current_cycle_used_hours,
            departure_at=departure_at,
        )
        return self._response_payload(route, plan_result)

    @staticmethod
    def _to_domain_segments(route: Route) -> tuple[RouteSegment, ...]:
        if len(route.legs) != 2:
            raise ValueError("A trip route must contain current-to-pickup and pickup-to-dropoff legs")
        return (
            RouteSegment(
                name=f"Current location to {route.legs[0].end.label}",
                distance_miles=route.legs[0].distance_miles,
                driving_minutes=route.legs[0].duration_minutes,
                stop_after=StopAction.PICKUP,
            ),
            RouteSegment(
                name=f"Pickup to {route.legs[1].end.label}",
                distance_miles=route.legs[1].distance_miles,
                driving_minutes=route.legs[1].duration_minutes,
                stop_after=StopAction.DROPOFF,
            ),
        )

    def _response_payload(self, route: Route, plan_result: PlanResult) -> dict:
        events = [self._event_payload(event) for event in plan_result.events]
        payload = {
            "status": "feasible" if plan_result.feasible else "infeasible",
            "route": self._route_payload(route),
            "events": events,
            "stops": [event for event in events if event["event_type"] != "DRIVING"],
            "daily_logs": self._daily_log_payload(plan_result),
            "summary": {
                "total_distance_miles": plan_result.total_distance_miles,
                "completed_distance_miles": plan_result.completed_distance_miles,
                "total_driving_minutes": plan_result.total_driving_minutes,
                "total_on_duty_minutes": plan_result.total_on_duty_minutes,
                "total_off_duty_minutes": plan_result.total_off_duty_minutes,
                "cycle_hours_used": plan_result.cycle_hours_used,
                "cycle_hours_remaining": plan_result.cycle_hours_remaining,
                "warnings": list(plan_result.warnings),
            },
            "error": None,
        }
        if not plan_result.feasible:
            payload["error"] = {
                "code": plan_result.error_code.value if plan_result.error_code else "UNKNOWN",
                "message": "The trip cannot finish within the available 70-hour cycle capacity.",
            }
        return payload

    @staticmethod
    def _route_payload(route: Route) -> dict:
        locations = [route.legs[0].start, *(leg.end for leg in route.legs)]
        return {
            "distance_miles": route.distance_miles,
            "duration_minutes": route.duration_minutes,
            "geometry": [[longitude, latitude] for longitude, latitude in route.geometry],
            "legs": [
                {
                    "start_label": leg.start.label,
                    "end_label": leg.end.label,
                    "distance_miles": leg.distance_miles,
                    "duration_minutes": leg.duration_minutes,
                }
                for leg in route.legs
            ],
            "waypoints": [
                {
                    "kind": kind,
                    "label": location.label,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                }
                for kind, location in zip(("current", "pickup", "dropoff"), locations)
            ],
        }

    @staticmethod
    def _event_payload(event: DutyEvent) -> dict:
        return {
            "event_type": event.event_type.value,
            "duty_status": event.duty_status.value,
            "start": event.start,
            "end": event.end,
            "duration_minutes": event.duration_minutes,
            "route_progress_miles": event.route_progress_miles,
            "reason": event.reason,
            "segment_index": event.segment_index,
            "segment_name": event.segment_name,
        }

    @staticmethod
    def _daily_log_payload(plan_result: PlanResult) -> list[dict]:
        totals_by_day = daily_duty_totals(plan_result.events)
        events_by_day: dict = {day: [] for day in totals_by_day}
        for event in plan_result.events:
            for day, event_slice in TripPlanningService._event_slices_by_day(event):
                events_by_day.setdefault(day, []).append(event_slice)

        return [
            {
                "date": day,
                "driving_minutes": totals.driving_minutes,
                "on_duty_not_driving_minutes": totals.on_duty_not_driving_minutes,
                "off_duty_minutes": totals.off_duty_minutes,
                "sleeper_berth_minutes": totals.sleeper_berth_minutes,
                "total_minutes": totals.total_minutes,
                "events": events_by_day[day],
            }
            for day, totals in sorted(totals_by_day.items())
        ]

    @staticmethod
    def _event_slices_by_day(event: DutyEvent):
        """Return event DTOs split at local midnight for daily log rendering."""

        cursor = event.start
        while cursor < event.end:
            next_day = cursor.date() + timedelta(days=1)
            midnight = datetime.combine(next_day, time.min, tzinfo=cursor.tzinfo)
            portion_end = min(event.end, midnight)
            payload = TripPlanningService._event_payload(event)
            payload["start"] = cursor
            payload["end"] = portion_end
            payload["duration_minutes"] = (portion_end - cursor).total_seconds() / 60
            yield cursor.date(), payload
            cursor = portion_end
