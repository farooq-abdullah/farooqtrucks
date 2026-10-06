from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.test import SimpleTestCase
from rest_framework.test import APIClient

from trips.clock import default_departure
from trips.services.routing import RouteLocator, RoutingError, geocode

INPUTS = {
    "current_location": "Chicago, IL",
    "pickup_location": "Springfield, IL",
    "dropoff_location": "St. Louis, MO",
    "current_cycle_used": 0,
}
LOCATIONS = [
    {"label": "Chicago, IL", "query": "Chicago, IL", "coordinates": [-87.63, 41.88]},
    {"label": "Springfield, IL", "query": "Springfield, IL", "coordinates": [-89.65, 39.78]},
    {"label": "St. Louis, MO", "query": "St. Louis, MO", "coordinates": [-90.2, 38.63]},
]


def example_route():
    legs = [
        {
            "distance_miles": 200,
            "duration_seconds": 4 * 3600,
            "geometry": {
                "type": "LineString",
                "coordinates": [LOCATIONS[0]["coordinates"], LOCATIONS[1]["coordinates"]],
            },
            "instructions": [],
        },
        {
            "distance_miles": 100,
            "duration_seconds": 2 * 3600,
            "geometry": {
                "type": "LineString",
                "coordinates": [LOCATIONS[1]["coordinates"], LOCATIONS[2]["coordinates"]],
            },
            "instructions": [],
        },
    ]
    return {
        "provider": "OSRM",
        "profile": "general road route",
        "legs": legs,
        "geometry": {"type": "LineString", "coordinates": [p["coordinates"] for p in LOCATIONS]},
        "distance_miles": 300,
        "driving_seconds": 6 * 3600,
    }


class APITests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_health_does_not_need_database(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["database_required"])

    @patch("trips.views.geocode")
    def test_invalid_inputs_never_call_map_service(self, geocode):
        for changes in (
            {"current_cycle_used": 71},
            {"current_cycle_used": -1},
            {"current_cycle_used": "NaN"},
            {"current_cycle_used": True},
            {"current_cycle_used": False},
            {"current_location": "   "},
        ):
            response = self.client.post("/api/trips/plan/", {**INPUTS, **changes}, format="json")
            self.assertEqual(response.status_code, 400)
        geocode.assert_not_called()

    def test_missing_required_fields(self):
        response = self.client.post("/api/trips/plan/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(response.data), 4)

    @patch("trips.views.geocode", side_effect=RoutingError("No location found."))
    def test_provider_failure_returns_clear_error(self, geocode):
        response = self.client.post("/api/trips/plan/", INPUTS, format="json")
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data["detail"], "No location found.")

    @patch("trips.views.annotate_schedule", return_value=[])
    @patch("trips.views.road_route", side_effect=lambda locations: example_route())
    @patch("trips.views.geocode", side_effect=LOCATIONS)
    def test_successful_plan_returns_route_schedule_and_logs(self, geocode, route, annotate):
        departure = datetime(2026, 10, 3, 8, tzinfo=ZoneInfo("America/Chicago"))
        with patch("trips.views.default_departure", return_value=departure):
            response = self.client.post("/api/trips/plan/", INPUTS, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["distance_miles"], 300)
        self.assertEqual(response.data["summary"]["elapsed_hours"], 8.5)
        self.assertEqual(response.data["summary"]["completion_time"], "2026-10-03T16:30:00-05:00")
        self.assertEqual(response.data["summary"]["inspections"], 2)
        self.assertEqual(response.data["daily_logs"][0]["total_hours"], 24)
        self.assertNotIn("assumptions", response.data)

    @patch("trips.views.annotate_schedule", return_value=[])
    @patch("trips.views.road_route", side_effect=lambda locations: example_route())
    @patch("trips.views.geocode", side_effect=LOCATIONS)
    def test_four_input_contract_uses_default_departure(self, geocode, route, annotate):
        response = self.client.post("/api/trips/plan/", INPUTS, format="json")
        self.assertEqual(response.status_code, 200)
        chicago_departure = default_departure(ZoneInfo("America/Chicago"))
        self.assertEqual(response.data["summary"]["departure_time"], chicago_departure.isoformat())
        self.assertEqual(response.data["planning_parameters"]["time_zone"], "America/Chicago")

    @patch("trips.views.annotate_schedule", return_value=[])
    @patch("trips.views.road_route", side_effect=lambda locations: example_route())
    @patch(
        "trips.views.geocode",
        side_effect=[
            {"label": "New York, NY", "query": "New York, NY", "coordinates": [-74.006, 40.713]},
            *LOCATIONS[1:],
        ],
    )
    def test_plan_infers_clock_from_starting_location(self, geocode, route, annotate):
        response = self.client.post(
            "/api/trips/plan/",
            {**INPUTS, "current_location": "New York, NY"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        new_york_departure = default_departure(ZoneInfo("America/New_York"))
        self.assertEqual(response.data["summary"]["departure_time"], new_york_departure.isoformat())
        self.assertEqual(response.data["planning_parameters"]["time_zone"], "America/New_York")

    def test_get_does_not_plan_or_call_providers(self):
        response = self.client.get("/api/trips/plan/")
        self.assertEqual(response.status_code, 405)


class RouteLocationTests(SimpleTestCase):
    @patch(
        "trips.services.routing.geocoding._geocoding_request",
        return_value=[
            {
                "display_name": "Milwaukee, WI",
                "lon": "-87.91",
                "lat": "43.04",
                "address": {"country_code": "us"},
            }
        ],
    )
    def test_cached_geocoding_avoids_duplicate_public_requests(self, request):
        cache.clear()
        first = geocode("Milwaukee, WI")
        second = geocode(" Milwaukee, WI ")
        self.assertEqual(first, second)
        request.assert_called_once()

    def test_interpolation_follows_bent_polyline(self):
        locator = RouteLocator(
            [{"distance_miles": 100, "geometry": {"coordinates": [[0, 0], [1, 0], [1, 1]]}}]
        )
        self.assertEqual(locator.at(0), [0, 0])
        self.assertEqual(locator.at(100), [1, 1])
        point = locator.at(75)
        self.assertAlmostEqual(point[0], 1)
        self.assertAlmostEqual(point[1], 0.5)

    def test_pickup_boundary_uses_end_of_first_leg(self):
        locator = RouteLocator(example_route()["legs"])
        self.assertEqual(locator.at(200), LOCATIONS[1]["coordinates"])
        self.assertEqual(locator.at(300), LOCATIONS[2]["coordinates"])
