from __future__ import annotations

from hashlib import sha256
from math import asin, cos, radians, sin, sqrt

from .base import GeocodedLocation, Route, RouteLeg, RoutingProvider


class MockRoutingProvider(RoutingProvider):
    """Deterministic local routing used until a real provider is introduced."""

    ROAD_DISTANCE_FACTOR = 1.2
    ASSUMED_SPEED_MPH = 50.0
    _LOCATIONS: dict[str, tuple[str, float, float]] = {
        "la plata, buenos aires, argentina": (
            "La Plata, Buenos Aires, Argentina",
            -34.9214,
            -57.9544,
        ),
        "buenos aires, argentina": (
            "Buenos Aires, Argentina",
            -34.6037,
            -58.3816,
        ),
        "rosario, santa fe, argentina": (
            "Rosario, Santa Fe, Argentina",
            -32.9442,
            -60.6505,
        ),
        "cordoba, argentina": ("Córdoba, Argentina", -31.4201, -64.1888),
        "chicago, il": ("Chicago, IL", 41.8781, -87.6298),
        "st. louis, mo": ("St. Louis, MO", 38.6270, -90.1994),
        "kansas city, mo": ("Kansas City, MO", 39.0997, -94.5786),
        "los angeles, ca": ("Los Angeles, CA", 34.0522, -118.2437),
        "dallas, tx": ("Dallas, TX", 32.7767, -96.7970),
        "new orleans, la": ("New Orleans, LA", 29.9511, -90.0715),
    }

    def geocode(self, query: str) -> GeocodedLocation:
        normalized = self._normalize(query)
        if normalized in self._LOCATIONS:
            label, latitude, longitude = self._LOCATIONS[normalized]
        else:
            latitude, longitude = self._fallback_coordinates(normalized)
            label = query.strip()
        return GeocodedLocation(
            query=query,
            label=label,
            latitude=latitude,
            longitude=longitude,
        )

    def calculate_route(self, locations: list[GeocodedLocation]) -> Route:
        if len(locations) < 2:
            raise ValueError("At least two locations are required to calculate a route")
        legs = tuple(
            self._leg(start, end) for start, end in zip(locations, locations[1:])
        )
        return Route(legs=legs)

    def _leg(self, start: GeocodedLocation, end: GeocodedLocation) -> RouteLeg:
        straight_line_miles = self._haversine_miles(
            start.latitude, start.longitude, end.latitude, end.longitude
        )
        distance_miles = round(max(1.0, straight_line_miles * self.ROAD_DISTANCE_FACTOR), 2)
        duration_minutes = round(distance_miles / self.ASSUMED_SPEED_MPH * 60, 2)
        return RouteLeg(
            start=start,
            end=end,
            distance_miles=distance_miles,
            duration_minutes=duration_minutes,
            geometry=((start.longitude, start.latitude), (end.longitude, end.latitude)),
        )

    @staticmethod
    def _normalize(query: str) -> str:
        return " ".join(query.lower().strip().split())

    @staticmethod
    def _fallback_coordinates(normalized_query: str) -> tuple[float, float]:
        digest = sha256(normalized_query.encode("utf-8")).digest()
        latitude = -55 + int.from_bytes(digest[:4], "big") / 2**32 * 33
        longitude = -73 + int.from_bytes(digest[4:8], "big") / 2**32 * 20
        return round(latitude, 6), round(longitude, 6)

    @staticmethod
    def _haversine_miles(
        start_lat: float, start_lon: float, end_lat: float, end_lon: float
    ) -> float:
        radius_miles = 3958.7613
        latitude_delta = radians(end_lat - start_lat)
        longitude_delta = radians(end_lon - start_lon)
        value = (
            sin(latitude_delta / 2) ** 2
            + cos(radians(start_lat))
            * cos(radians(end_lat))
            * sin(longitude_delta / 2) ** 2
        )
        return radius_miles * 2 * asin(sqrt(value))
