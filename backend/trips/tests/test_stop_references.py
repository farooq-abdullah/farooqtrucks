"""Driver-facing stop references must remain useful without a public lookup."""

from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase

from trips.services.routing import RouteLocator, annotate_schedule
from trips.services.routing.client import RoutingError
from trips.services.routing.geocoding import reverse_label
from trips.services.routing.place_reference import _places, _reference


class StopReferenceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        _places.cache_clear()
        _reference.cache_clear()

    def tearDown(self):
        _places.cache_clear()
        _reference.cache_clear()

    def fallback_locator(self):
        return RouteLocator(
            [
                {
                    "distance_miles": 100,
                    "geometry": {"coordinates": [[-83.3, 39.98], [-83.2, 39.98]]},
                    "instructions": [{"road": "I 70", "distance_miles": 100}],
                }
            ]
        )

    @patch(
        "trips.services.routing.place_reference.gzip.open", side_effect=EOFError("Truncated gzip")
    )
    def test_truncated_place_index_keeps_usable_road_reference(self, source):
        self.assertEqual(self.fallback_locator().reference_at(50), "On I 70 · 50 mi into trip")

    @patch("trips.services.routing.place_reference.json.load", return_value={"places": []})
    def test_empty_place_index_keeps_usable_road_reference(self, source):
        self.assertEqual(self.fallback_locator().reference_at(50), "On I 70 · 50 mi into trip")

    @patch("trips.services.routing.geocoding._geocoding_request", return_value={"address": {}})
    def test_ohio_stop_has_named_reference_instead_of_bare_coordinates(self, request):
        label = reverse_label([-83.2279, 39.9807])
        self.assertRegex(label, r"^(Near|About).*?, OH$")
        self.assertNotIn("39.9807", label)
        request.assert_not_called()

    @patch("trips.services.routing.geocoding._geocoding_request", return_value={"address": {}})
    def test_pennsylvania_fuel_area_has_named_reference(self, request):
        label = reverse_label([-75.9747, 40.5657])
        self.assertRegex(label, r"^(Near|About).*?, PA$")
        self.assertNotIn("-75.9747", label)
        request.assert_not_called()

    @patch(
        "trips.services.routing.locations.reverse_label", side_effect=RoutingError("Unavailable")
    )
    def test_unavailable_place_lookup_falls_back_to_road_and_trip_mileage(self, reverse):
        route = {
            "legs": [
                {
                    "distance_miles": 100,
                    "geometry": {"coordinates": [[-83.3, 39.98], [-83.2, 39.98]]},
                    "instructions": [{"road": "I 70", "distance_miles": 100}],
                }
            ]
        }
        locations = [
            {"label": "Origin", "coordinates": [-83.3, 39.98]},
            {"label": "Destination", "coordinates": [-83.2, 39.98]},
        ]
        event = {
            "start_route_miles": 50,
            "end_route_miles": 50,
            "location": "Along route",
            "status": "off_duty",
        }
        annotate_schedule([event], route, locations)
        self.assertEqual(event["location"], "On I 70 · 50 mi into trip")
        self.assertAlmostEqual(event["coordinates"][0], -83.25)
        self.assertTrue(event["location_estimated"])
