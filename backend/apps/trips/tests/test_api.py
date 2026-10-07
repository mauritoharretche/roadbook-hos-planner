from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import patch

from django.test import Client
import pytest

from apps.trips.services.trip_planning import TripPlanningService
from apps.trips.routing import RoutingUpstreamError


def post_json(client: Client, path: str, payload: object):
    return client.post(path, data=payload, content_type="application/json")


def valid_trip_payload(**overrides):
    payload = {
        "current_location": "La Plata, Buenos Aires, Argentina",
        "pickup_location": "Buenos Aires, Argentina",
        "dropoff_location": "Rosario, Santa Fe, Argentina",
        "current_cycle_used_hours": 10,
        "departure_at": "2026-01-05T08:00:00Z",
    }
    payload.update(overrides)
    return payload


def long_trip_payload(**overrides):
    payload = {
        "current_location": "Los Angeles, CA",
        "pickup_location": "Dallas, TX",
        "dropoff_location": "New Orleans, LA",
        "current_cycle_used_hours": 10,
        "departure_at": "2026-10-07T08:00:00Z",
    }
    payload.update(overrides)
    return payload


def short_trip_payload(**overrides):
    payload = {
        "current_location": "Chicago, IL",
        "pickup_location": "St. Louis, MO",
        "dropoff_location": "Kansas City, MO",
        "current_cycle_used_hours": 10,
        "departure_at": "2026-10-07T08:00:00Z",
    }
    payload.update(overrides)
    return payload


def test_health_endpoint():
    response = Client().get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_valid_geocoding_request_uses_mock_provider():
    response = post_json(
        Client(),
        "/api/v1/locations/geocode",
        {"query": "La Plata, Buenos Aires, Argentina"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": "La Plata, Buenos Aires, Argentina",
        "label": "La Plata, Buenos Aires, Argentina",
        "latitude": -34.9214,
        "longitude": -57.9544,
    }


def test_invalid_geocoding_request_returns_400():
    response = post_json(Client(), "/api/v1/locations/geocode", {"query": "  "})

    assert response.status_code == 400
    assert "query" in response.json()


def test_geocoding_rejects_invalid_payload_shape():
    response = post_json(Client(), "/api/v1/locations/geocode", ["La Plata"])

    assert response.status_code == 400


def test_geocoding_maps_provider_failure_to_502():
    with patch(
        "apps.trips.api.views.get_routing_provider",
        side_effect=RoutingUpstreamError("OpenRouteService request failed"),
    ):
        response = post_json(Client(), "/api/v1/locations/geocode", {"query": "La Plata"})

    assert response.status_code == 502
    assert response.json()["detail"] == "OpenRouteService request failed"


def test_valid_trip_planning_request_returns_route_events_and_daily_logs():
    response = post_json(Client(), "/api/v1/trips/plan", valid_trip_payload())
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "feasible"
    assert body["route"]["distance_miles"] > 0
    assert len(body["route"]["legs"]) == 2
    assert body["route"]["geometry"]
    assert [waypoint["kind"] for waypoint in body["route"]["waypoints"]] == [
        "current",
        "pickup",
        "dropoff",
    ]
    assert [event["event_type"] for event in body["events"]] == [
        "DRIVING",
        "PICKUP",
        "DRIVING",
        "DROPOFF",
    ]
    assert [stop["event_type"] for stop in body["stops"]] == ["PICKUP", "DROPOFF"]
    assert len(body["daily_logs"]) == 1
    assert body["error"] is None


def test_invalid_trip_planning_request_returns_400():
    payload = valid_trip_payload()
    del payload["pickup_location"]

    response = post_json(Client(), "/api/v1/trips/plan", payload)

    assert response.status_code == 400
    assert "pickup_location" in response.json()


def test_infeasible_cycle_is_valid_api_response_not_server_error():
    response = post_json(
        Client(),
        "/api/v1/trips/plan",
        valid_trip_payload(current_cycle_used_hours=70),
    )
    body = response.json()

    assert response.status_code == 422
    assert body["status"] == "infeasible"
    assert body["error"]["code"] == "CYCLE_CAPACITY_EXHAUSTED"
    assert body["events"] == []
    assert body["summary"]["cycle_hours_used"] == 70


def test_feasible_plan_exposes_chronological_non_empty_daily_logs_with_consistent_totals():
    response = post_json(Client(), "/api/v1/trips/plan", valid_trip_payload())
    body = response.json()

    assert response.status_code == 200
    assert "daily_logs" in body
    assert body["daily_logs"]

    for daily_log in body["daily_logs"]:
        events = daily_log["events"]
        assert events
        assert events == sorted(events, key=lambda event: event["start"])
        assert sum(event["duration_minutes"] for event in events) == daily_log[
            "total_minutes"
        ]
        assert sum(
            event["duration_minutes"]
            for event in events
            if event["duty_status"] == "DRIVING"
        ) == daily_log["driving_minutes"]
        assert sum(
            event["duration_minutes"]
            for event in events
            if event["duty_status"] == "ON_DUTY_NOT_DRIVING"
        ) == daily_log["on_duty_not_driving_minutes"]
        assert sum(
            event["duration_minutes"]
            for event in events
            if event["duty_status"] == "OFF_DUTY"
        ) == daily_log["off_duty_minutes"]


def test_api_preserves_domain_planner_result():
    payload = valid_trip_payload()
    response = post_json(Client(), "/api/v1/trips/plan", payload)
    body = response.json()

    service_payload = TripPlanningService.with_mock_routing().plan_trip(
        current_location=payload["current_location"],
        pickup_location=payload["pickup_location"],
        dropoff_location=payload["dropoff_location"],
        current_cycle_used_hours=payload["current_cycle_used_hours"],
        departure_at=datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc),
    )

    assert body["summary"] == service_payload["summary"]
    assert body["events"] == [
        {
            **event,
            "start": event["start"].isoformat().replace("+00:00", "Z"),
            "end": event["end"].isoformat().replace("+00:00", "Z"),
        }
        for event in service_payload["events"]
    ]


def test_long_mock_trip_daily_logs_stop_on_trip_end_date_without_changing_hos_output():
    response = post_json(Client(), "/api/v1/trips/plan", long_trip_payload())
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "feasible"
    assert datetime.fromisoformat(body["events"][-1]["end"].replace("Z", "+00:00")).date() == date(
        2026, 10, 10
    )

    daily_log_dates = [daily_log["date"] for daily_log in body["daily_logs"]]
    assert daily_log_dates == ["2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10"]
    assert daily_log_dates == sorted(daily_log_dates)
    assert "2026-10-11" not in daily_log_dates
    assert all(
        daily_log["events"] == sorted(daily_log["events"], key=lambda event: event["start"])
        for daily_log in body["daily_logs"]
    )

    assert [event["event_type"] for event in body["events"]] == [
        "DRIVING",
        "BREAK_30_MIN",
        "DRIVING",
        "REST_10_HOURS",
        "DRIVING",
        "BREAK_30_MIN",
        "DRIVING",
        "FUEL",
        "DRIVING",
        "REST_10_HOURS",
        "DRIVING",
        "PICKUP",
        "DRIVING",
        "REST_10_HOURS",
        "DRIVING",
        "FUEL",
        "DRIVING",
        "DROPOFF",
    ]
    assert [(event["event_type"], event["start"], event["end"]) for event in body["events"]] == [
        ("DRIVING", "2026-10-07T08:00:00Z", "2026-10-07T16:00:00Z"),
        ("BREAK_30_MIN", "2026-10-07T16:00:00Z", "2026-10-07T16:30:00Z"),
        ("DRIVING", "2026-10-07T16:30:00Z", "2026-10-07T19:30:00Z"),
        ("REST_10_HOURS", "2026-10-07T19:30:00Z", "2026-10-08T05:30:00Z"),
        ("DRIVING", "2026-10-08T05:30:00Z", "2026-10-08T13:30:00Z"),
        ("BREAK_30_MIN", "2026-10-08T13:30:00Z", "2026-10-08T14:00:00Z"),
        ("DRIVING", "2026-10-08T14:00:00Z", "2026-10-08T14:59:59.838419Z"),
        ("FUEL", "2026-10-08T14:59:59.838419Z", "2026-10-08T15:29:59.838419Z"),
        ("DRIVING", "2026-10-08T15:29:59.838419Z", "2026-10-08T17:30:00Z"),
        ("REST_10_HOURS", "2026-10-08T17:30:00Z", "2026-10-09T03:30:00Z"),
        ("DRIVING", "2026-10-09T03:30:00Z", "2026-10-09T11:12:22.800000Z"),
        ("PICKUP", "2026-10-09T11:12:22.800000Z", "2026-10-09T12:12:22.800000Z"),
        ("DRIVING", "2026-10-09T12:12:22.800000Z", "2026-10-09T15:30:00Z"),
        ("REST_10_HOURS", "2026-10-09T15:30:00Z", "2026-10-10T01:30:00Z"),
        ("DRIVING", "2026-10-10T01:30:00Z", "2026-10-10T08:29:59.760000Z"),
        ("FUEL", "2026-10-10T08:29:59.760000Z", "2026-10-10T08:59:59.760000Z"),
        ("DRIVING", "2026-10-10T08:59:59.760000Z", "2026-10-10T09:18:58.800000Z"),
        ("DROPOFF", "2026-10-10T09:18:58.800000Z", "2026-10-10T10:18:58.800000Z"),
    ]
    assert body["summary"] == {
        "total_distance_miles": 2015.82,
        "completed_distance_miles": pytest.approx(2015.82),
        "total_driving_minutes": pytest.approx(2418.98),
        "total_on_duty_minutes": pytest.approx(2598.98),
        "total_off_duty_minutes": 1860.0,
        "cycle_hours_used": pytest.approx(53.31633333333334),
        "cycle_hours_remaining": pytest.approx(16.68366666666666),
        "warnings": [
            "Cycle availability is calculated from the supplied aggregate hours only; "
            "no 8-day rollover or restart is assumed."
        ],
    }


def test_short_mock_trip_keeps_its_existing_planning_behavior():
    response = post_json(Client(), "/api/v1/trips/plan", short_trip_payload())
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "feasible"
    assert [event["event_type"] for event in body["events"]] == [
        "DRIVING",
        "PICKUP",
        "DRIVING",
        "REST_10_HOURS",
        "DRIVING",
        "DROPOFF",
    ]
    assert [daily_log["date"] for daily_log in body["daily_logs"]] == [
        "2026-10-07",
        "2026-10-08",
    ]
    assert body["summary"]["total_distance_miles"] == 600.15
    assert body["summary"]["total_on_duty_minutes"] == pytest.approx(840.18)
