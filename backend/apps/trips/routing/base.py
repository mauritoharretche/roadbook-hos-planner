from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class RoutingProviderError(Exception):
    """A recoverable provider configuration, network, or response failure."""


class RoutingUpstreamError(RoutingProviderError):
    """The upstream provider timed out or returned an unsuccessful response."""


class RoutingResponseError(RoutingProviderError):
    """The upstream provider returned data outside the expected contract."""


@dataclass(frozen=True)
class GeocodedLocation:
    query: str
    label: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class RouteLeg:
    start: GeocodedLocation
    end: GeocodedLocation
    distance_miles: float
    duration_minutes: float
    geometry: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class Route:
    legs: tuple[RouteLeg, ...]

    @property
    def distance_miles(self) -> float:
        return sum(leg.distance_miles for leg in self.legs)

    @property
    def duration_minutes(self) -> float:
        return sum(leg.duration_minutes for leg in self.legs)

    @property
    def geometry(self) -> tuple[tuple[float, float], ...]:
        coordinates: list[tuple[float, float]] = []
        for leg in self.legs:
            if not coordinates:
                coordinates.extend(leg.geometry)
            else:
                coordinates.extend(leg.geometry[1:])
        return tuple(coordinates)


class RoutingProvider(ABC):
    """Small provider boundary to replace with OpenRouteService in a later phase."""

    @abstractmethod
    def geocode(self, query: str) -> GeocodedLocation:
        raise NotImplementedError

    @abstractmethod
    def calculate_route(self, locations: list[GeocodedLocation]) -> Route:
        raise NotImplementedError
