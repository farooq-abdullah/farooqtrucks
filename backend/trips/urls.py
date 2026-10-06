from django.urls import path

from .views import health, location_search, plan_trip

urlpatterns = [
    path("health/", health),
    path("locations/search/", location_search),
    path("trips/plan/", plan_trip),
]
