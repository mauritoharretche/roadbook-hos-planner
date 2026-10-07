from django.urls import path

from .views import geocode_location, plan_trip

urlpatterns = [
    path("locations/geocode", geocode_location, name="location-geocode"),
    path("trips/plan", plan_trip, name="trip-plan"),
]
