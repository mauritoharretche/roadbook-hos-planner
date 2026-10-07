from rest_framework import serializers


class GeocodeRequestSerializer(serializers.Serializer):
    query = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)


class GeocodeResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    label = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(allow_blank=False, trim_whitespace=True)
    pickup_location = serializers.CharField(allow_blank=False, trim_whitespace=True)
    dropoff_location = serializers.CharField(allow_blank=False, trim_whitespace=True)
    current_cycle_used_hours = serializers.FloatField(min_value=0, max_value=70)
    departure_at = serializers.DateTimeField(required=False)


class RouteLegResponseSerializer(serializers.Serializer):
    start_label = serializers.CharField()
    end_label = serializers.CharField()
    distance_miles = serializers.FloatField()
    duration_minutes = serializers.FloatField()


class RouteWaypointResponseSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["current", "pickup", "dropoff"])
    label = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class RouteResponseSerializer(serializers.Serializer):
    distance_miles = serializers.FloatField()
    duration_minutes = serializers.FloatField()
    geometry = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))
    legs = RouteLegResponseSerializer(many=True)
    waypoints = RouteWaypointResponseSerializer(many=True)


class PlannedEventResponseSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    duty_status = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    duration_minutes = serializers.FloatField()
    route_progress_miles = serializers.FloatField()
    reason = serializers.CharField()
    segment_index = serializers.IntegerField(allow_null=True)
    segment_name = serializers.CharField(allow_null=True)


class DailyLogResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    driving_minutes = serializers.FloatField()
    on_duty_not_driving_minutes = serializers.FloatField()
    off_duty_minutes = serializers.FloatField()
    sleeper_berth_minutes = serializers.FloatField()
    total_minutes = serializers.FloatField()
    events = PlannedEventResponseSerializer(many=True)


class PlanSummaryResponseSerializer(serializers.Serializer):
    total_distance_miles = serializers.FloatField()
    completed_distance_miles = serializers.FloatField()
    total_driving_minutes = serializers.FloatField()
    total_on_duty_minutes = serializers.FloatField()
    total_off_duty_minutes = serializers.FloatField()
    cycle_hours_used = serializers.FloatField()
    cycle_hours_remaining = serializers.FloatField()
    warnings = serializers.ListField(child=serializers.CharField())


class PlanErrorResponseSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class TripPlanResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["feasible", "infeasible"])
    route = RouteResponseSerializer()
    events = PlannedEventResponseSerializer(many=True)
    stops = PlannedEventResponseSerializer(many=True)
    daily_logs = DailyLogResponseSerializer(many=True)
    summary = PlanSummaryResponseSerializer()
    error = PlanErrorResponseSerializer(allow_null=True)
