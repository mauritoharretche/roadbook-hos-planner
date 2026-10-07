from django.conf import settings

from .base import RoutingProvider, RoutingProviderError
from .mock import MockRoutingProvider
from .ors import OpenRouteServiceRoutingProvider


def get_routing_provider() -> RoutingProvider:
    if settings.ROUTING_PROVIDER == "mock":
        return MockRoutingProvider()
    if settings.ROUTING_PROVIDER == "ors":
        return OpenRouteServiceRoutingProvider(settings.ORS_API_KEY)
    raise RoutingProviderError(
        f"Unsupported ROUTING_PROVIDER '{settings.ROUTING_PROVIDER}'. Use 'mock' or 'ors'."
    )
