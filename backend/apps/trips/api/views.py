from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    GeocodeRequestSerializer,
    GeocodeResponseSerializer,
    TripPlanRequestSerializer,
    TripPlanResponseSerializer,
)
from apps.trips.domain.hos import HOSPlanner
from apps.trips.routing import RoutingProviderError, get_routing_provider
from apps.trips.services.trip_planning import TripPlanningService


def _service() -> TripPlanningService:
    return TripPlanningService(routing_provider=get_routing_provider(), planner=HOSPlanner())


@api_view(["GET"])
def health(_: Request) -> Response:
    return Response({"status": "ok"})


@api_view(["POST"])
def geocode_location(request: Request) -> Response:
    serializer = GeocodeRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        payload = _service().geocode(serializer.validated_data["query"])
    except RoutingProviderError as error:
        return Response({"detail": str(error)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response(GeocodeResponseSerializer(payload).data)


@api_view(["POST"])
def plan_trip(request: Request) -> Response:
    serializer = TripPlanRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        payload = _service().plan_trip(
            current_location=data["current_location"],
            pickup_location=data["pickup_location"],
            dropoff_location=data["dropoff_location"],
            current_cycle_used_hours=data["current_cycle_used_hours"],
            departure_at=data.get("departure_at") or timezone.now(),
        )
    except RoutingProviderError as error:
        return Response({"detail": str(error)}, status=status.HTTP_502_BAD_GATEWAY)
    response_status = (
        status.HTTP_200_OK
        if payload["status"] == "feasible"
        else status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    return Response(TripPlanResponseSerializer(payload).data, status=response_status)
