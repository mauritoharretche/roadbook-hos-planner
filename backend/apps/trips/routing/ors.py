from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .base import (
    GeocodedLocation,
    Route,
    RouteLeg,
    RoutingProvider,
    RoutingResponseError,
    RoutingUpstreamError,
)


class OpenRouteServiceRoutingProvider(RoutingProvider):
    """Server-side adapter for ORS geocoding and GeoJSON driving directions."""

    base_url = "https://api.heigit.org"
    timeout_seconds = 10

    def __init__(self, api_key: str) -> None:
        if not api_key.strip():
            raise RoutingUpstreamError("OpenRouteService is selected but ORS_API_KEY is not configured")
        self.api_key = api_key

    def geocode(self, query: str) -> GeocodedLocation:
        normalized_query = query.strip()
        try:
            response = self._fetch_json(
                f"{self.base_url}/pelias/v1/search?{urlencode({'text': normalized_query, 'size': 1})}"
            )
            feature = response["features"][0]
            longitude, latitude = feature["geometry"]["coordinates"][:2]
            properties = feature.get("properties", {})
            label = properties.get("label") or properties.get("name") or normalized_query
            return GeocodedLocation(
                query=query,
                label=str(label),
                latitude=float(latitude),
                longitude=float(longitude),
            )
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise RoutingResponseError("OpenRouteService returned an invalid geocoding response") from error

    def calculate_route(self, locations: list[GeocodedLocation]) -> Route:
        if len(locations) < 2:
            raise ValueError("At least two locations are required to calculate a route")
        return Route(legs=tuple(self._route_leg(start, end) for start, end in zip(locations, locations[1:])))

    def _route_leg(self, start: GeocodedLocation, end: GeocodedLocation) -> RouteLeg:
        response = self._fetch_json(
            f"{self.base_url}/openrouteservice/v2/directions/driving-car/geojson",
            payload={"coordinates": [[start.longitude, start.latitude], [end.longitude, end.latitude]]},
        )
        try:
            feature = response["features"][0]
            summary = feature["properties"]["summary"]
            coordinates = tuple(
                (float(longitude), float(latitude))
                for longitude, latitude, *_ in feature["geometry"]["coordinates"]
            )
            if len(coordinates) < 2:
                raise ValueError("Route geometry has fewer than two points")
            return RouteLeg(
                start=start,
                end=end,
                distance_miles=float(summary["distance"]) / 1609.344,
                duration_minutes=float(summary["duration"]) / 60,
                geometry=coordinates,
            )
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise RoutingResponseError("OpenRouteService returned an invalid directions response") from error

    def _fetch_json(self, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            url,
            data=data,
            headers={
                "Authorization": self.api_key,
                "Accept": "application/json, application/geo+json",
                **({"Content-Type": "application/json"} if data is not None else {}),
            },
            method="POST" if data is not None else "GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - fixed API host
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise RoutingUpstreamError("OpenRouteService request failed") from error
