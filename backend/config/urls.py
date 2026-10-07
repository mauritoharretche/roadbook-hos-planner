from django.urls import include, path

from apps.trips.api.views import health

urlpatterns = [
    path("api/health", health, name="health"),
    path("api/v1/", include("apps.trips.api.urls")),
]
