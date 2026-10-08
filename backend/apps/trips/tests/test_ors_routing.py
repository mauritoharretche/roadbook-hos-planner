import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from apps.trips.routing import (
    GeocodedLocation,
    OpenRouteServiceRoutingProvider,
    RoutingResponseError,
    RoutingUpstreamError,
)


def provider() -> OpenRouteServiceRoutingProvider:
    return OpenRouteServiceRoutingProvider("test-api-key")


def test_ors_geocoding_transforms_successful_response():
    routing_provider = provider()
    with patch.object(
        routing_provider,
        "_fetch_json",
        return_value={
            "features": [
                {
                    "geometry": {"coordinates": [-57.9544, -34.9214]},
                    "properties": {"label": "La Plata, Buenos Aires, Argentina"},
                }
            ]
        },
    ) as fetch:
        location = routing_provider.geocode("La Plata")

    assert location.label == "La Plata, Buenos Aires, Argentina"
    assert location.latitude == -34.9214
    assert location.longitude == -57.9544
    assert fetch.called


def test_ors_uses_heigit_geocoding_and_directions_endpoints():
    start = GeocodedLocation("La Plata", "La Plata", -34.9214, -57.9544)
    end = GeocodedLocation("Buenos Aires", "Buenos Aires", -34.6037, -58.3816)
    response = MagicMock()
    response.__enter__.return_value.read.side_effect = [
        json.dumps(
            {
                "features": [
                    {
                        "geometry": {"coordinates": [-57.9544, -34.9214]},
                        "properties": {"label": "La Plata, Buenos Aires, Argentina"},
                    }
                ]
            }
        ).encode("utf-8"),
        json.dumps(
            {
                "features": [
                    {
                        "properties": {"summary": {"distance": 1609.344, "duration": 3600}},
                        "geometry": {"coordinates": [[-57.9544, -34.9214], [-58.3816, -34.6037]]},
                    }
                ]
            }
        ).encode("utf-8"),
    ]

    with patch("apps.trips.routing.ors.urlopen", return_value=response) as urlopen:
        provider().geocode("La Plata")
        provider().calculate_route([start, end])

    geocode_request = urlopen.call_args_list[0].args[0]
    directions_request = urlopen.call_args_list[1].args[0]
    assert geocode_request.full_url == "https://api.heigit.org/pelias/v1/search?text=La+Plata&size=1"
    assert geocode_request.method == "GET"
    assert directions_request.full_url == (
        "https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson"
    )
    assert directions_request.method == "POST"
    assert directions_request.get_header("Authorization") == "test-api-key"


def test_ors_route_transforms_geojson_per_leg():
    routing_provider = provider()
    responses = [
        {
            "features": [
                {
                    "properties": {"summary": {"distance": 1609.344, "duration": 3600}},
                    "geometry": {"coordinates": [[-58.0, -34.0], [-58.2, -34.2]]},
                }
            ]
        },
        {
            "features": [
                {
                    "properties": {"summary": {"distance": 3218.688, "duration": 7200}},
                    "geometry": {"coordinates": [[-58.2, -34.2], [-60.0, -32.0]]},
                }
            ]
        },
    ]
    locations = [
        GeocodedLocation("a", "A", -34.0, -58.0),
        GeocodedLocation("b", "B", -34.2, -58.2),
        GeocodedLocation("c", "C", -32.0, -60.0),
    ]

    with patch.object(routing_provider, "_fetch_json", side_effect=responses) as fetch:
        route = routing_provider.calculate_route(locations)

    assert len(route.legs) == 2
    assert route.distance_miles == pytest.approx(3)
    assert route.duration_minutes == pytest.approx(180)
    assert route.geometry == ((-58.0, -34.0), (-58.2, -34.2), (-60.0, -32.0))
    assert fetch.call_count == 2


def test_ors_timeout_becomes_routing_upstream_error():
    with patch("apps.trips.routing.ors.urlopen", side_effect=TimeoutError):
        with pytest.raises(RoutingUpstreamError, match="request failed"):
            provider()._fetch_json("https://api.heigit.org/pelias/v1/search?text=x")


def test_ors_http_error_becomes_routing_upstream_error():
    upstream_error = HTTPError("https://api.heigit.org", 429, "rate limited", None, None)
    with patch("apps.trips.routing.ors.urlopen", side_effect=upstream_error):
        with pytest.raises(RoutingUpstreamError, match="request failed"):
            provider()._fetch_json("https://api.heigit.org/pelias/v1/search?text=x")


def test_ors_malformed_geocode_response_becomes_routing_response_error():
    routing_provider = provider()
    with patch.object(routing_provider, "_fetch_json", return_value={"features": []}):
        with pytest.raises(RoutingResponseError, match="invalid geocoding"):
            routing_provider.geocode("La Plata")
