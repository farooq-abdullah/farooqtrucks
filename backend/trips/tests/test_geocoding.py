from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient

from trips.services.routing import LocationError, RoutingError, geocode, suggest_locations

from .test_api import INPUTS


def photon_place(name, country, country_code, coordinates, state=None):
    return {
        "properties": {
            "name": name,
            "state": state,
            "country": country,
            "countrycode": country_code,
        },
        "geometry": {"coordinates": coordinates},
    }


class GeocodingTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    @patch(
        "trips.services.routing.geocoding._geocoding_request",
        return_value=[
            {
                "display_name": "Tokyo, Japan",
                "lon": "139.76",
                "lat": "35.68",
                "address": {"country_code": "jp"},
            }
        ],
    )
    def test_tokio_is_searched_globally_and_not_substituted_with_us_namesake(self, request):
        with self.assertRaisesRegex(LocationError, "Tokyo, Japan"):
            geocode("Tokio")
        params = request.call_args.args[1]
        self.assertNotIn("countrycodes", params)

    @patch(
        "trips.services.routing.geocoding._geocoding_request",
        return_value=[
            {
                "display_name": "Toronto, Canada",
                "lon": "-79.38",
                "lat": "43.65",
                "address": {"country_code": "ca"},
            }
        ],
    )
    def test_country_is_checked_even_inside_us_bounding_rectangle(self, request):
        with self.assertRaises(LocationError):
            geocode("Toronto")

    @patch(
        "trips.services.routing.geocoding._geocoding_request",
        return_value=[
            {
                "display_name": "Anchorage, Alaska, United States",
                "lon": "-149.9",
                "lat": "61.2",
                "address": {"country_code": "us"},
            }
        ],
    )
    def test_noncontiguous_us_is_rejected(self, request):
        with self.assertRaises(LocationError):
            geocode("Anchorage, AK")

    @patch(
        "trips.services.routing.geocoding._suggestions_request",
        return_value={
            "features": [
                photon_place("Tokyo", "Japan", "JP", [139.76, 35.68]),
                photon_place("Tokio", "United States", "US", [-98.82, 47.92], "North Dakota"),
            ]
        },
    )
    def test_suggestions_keep_country_and_mark_foreign_match_unavailable(self, request):
        results = suggest_locations("Tokio")
        self.assertEqual(results[0]["label"], "Tokyo, Japan")
        self.assertFalse(results[0]["supported"])
        self.assertTrue(results[1]["supported"])
        self.assertIn("North Dakota", results[1]["label"])
        self.assertEqual(suggest_locations(" tokio "), results)
        request.assert_called_once()


class LocationSearchAPITests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    @patch("trips.views.suggest_locations")
    def test_short_and_overlong_queries_do_not_call_provider(self, provider):
        for query in ("", "a", "a" * 201):
            self.assertEqual(
                self.client.get("/api/locations/search/", {"q": query}).status_code, 400
            )
        provider.assert_not_called()

    @patch("trips.views.suggest_locations", return_value=[])
    def test_search_has_separate_budget_from_trip_planning(self, provider):
        for _ in range(35):
            self.assertEqual(
                self.client.get("/api/locations/search/", {"q": "Chicago"}).status_code, 200
            )
        # This request reaches validation rather than exhausting the 30/hour trip budget.
        self.assertEqual(self.client.post("/api/trips/plan/", {}, format="json").status_code, 400)

    @patch("trips.views.suggest_locations", side_effect=RoutingError("Search unavailable."))
    def test_provider_error_returns_502(self, provider):
        response = self.client.get("/api/locations/search/", {"q": "Chicago"})
        self.assertEqual(response.status_code, 502)

    @patch("trips.views.road_route")
    @patch(
        "trips.views.geocode",
        side_effect=LocationError("Choose a location in the contiguous United States."),
    )
    def test_foreign_place_returns_field_error_without_requesting_route(self, geocoder, route):
        response = self.client.post(
            "/api/trips/plan/", {**INPUTS, "current_location": "Tokyo"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("current_location", response.data)
        route.assert_not_called()


class SearchReliabilityTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    @patch("trips.services.routing.geocoding._geocoding_request")
    @patch("trips.services.routing.geocoding._suggestions_request")
    def test_popular_aliases_resolve_locally_to_the_selected_verified_city(self, search, geocoder):
        expected = {
            "NY": "New York",
            "nyc": "New York",
            "LA": "Los Angeles",
            "SF": "San Francisco",
            "DC": "Washington",
            "Vegas": "Las Vegas",
            "CHI": "Chicago",
            "ATL": "Atlanta",
            "Philly": "Philadelphia",
            "PHX": "Phoenix",
            "STL": "Saint Louis",
            "NOLA": "New Orleans",
        }
        for alias, city in expected.items():
            with self.subTest(alias=alias):
                suggestions = suggest_locations(alias)
                self.assertEqual(suggestions[0]["primary"], city)
                self.assertTrue(suggestions[0]["supported"])
                self.assertIn("United States", suggestions[0]["label"])
                location = geocode(alias)
                cache.clear()  # A new serverless instance must resolve the same selection.
                selected = geocode(suggestions[0]["label"])
                self.assertEqual(location["coordinates"], selected["coordinates"])
        search.assert_not_called()
        geocoder.assert_not_called()

    def test_state_abbreviations_remain_state_context(self):
        from trips.services.routing.place_names import expand_query

        self.assertEqual(expand_query("Baton Rouge, LA"), "Baton Rouge, Louisiana, United States")
        self.assertEqual(expand_query("Albany NY"), "Albany, New York, United States")
        self.assertEqual(
            expand_query("123 Main Street, Austin, TX 78701"),
            "123 Main Street, Austin, Texas, 78701, United States",
        )

    @patch("trips.services.routing.geocoding._suggestions_request")
    def test_partial_springfield_is_immediate_and_keeps_distinct_states(self, search):
        suggestions = suggest_locations("Springfie")
        self.assertTrue(any("Illinois" in p["label"] for p in suggestions))
        self.assertTrue(any("Massachusetts" in p["label"] for p in suggestions))
        self.assertTrue(all(p["primary"] == "Springfield" for p in suggestions))
        search.assert_not_called()
        with self.assertRaisesRegex(LocationError, "several cities"):
            geocode("Springfield")
        self.assertIn("Illinois", geocode("Springfield, IL")["label"])

    @patch("trips.views.suggest_locations", return_value=[])
    def test_two_character_alias_reaches_search(self, search):
        response = APIClient().get("/api/locations/search/", {"q": "LA"})
        self.assertEqual(response.status_code, 200)
        search.assert_called_once_with("LA")

    @override_settings(GEOCODING_PROVIDER="photon", GEOCODING_BASE_URL="https://example.test")
    @patch("trips.services.routing.client._request")
    def test_photon_forward_and_reverse_adapter(self, request):
        from trips.services.routing.client import _geocoding_request

        place = photon_place("Madison", "United States", "US", [-89.4, 43.07], "Wisconsin")
        place["properties"]["city"] = "Madison"
        request.return_value = {"features": [place]}
        result = _geocoding_request("search", {"q": "Madison, Wisconsin", "limit": 6})
        self.assertEqual(result[0]["address"]["city"], "Madison")
        self.assertEqual(result[0]["address"]["country_code"], "us")
        self.assertEqual(request.call_args.args[0], "https://example.test/api/")
        result = _geocoding_request("reverse", {"lon": -89.4, "lat": 43.07})
        self.assertEqual(result["address"]["state"], "Wisconsin")
        self.assertEqual(request.call_args.kwargs["timeout"], (1, 2))

    def test_new_search_does_not_wait_for_old_network_request(self):
        from trips.services.routing.client import _suggestions_request

        started, release = Event(), Event()

        def upstream(url, params, **kwargs):
            if params["q"] == "old":
                started.set()
                release.wait(2)
            return {"features": [], "query": params["q"]}

        with patch("trips.services.routing.client._request", side_effect=upstream):
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(_suggestions_request, {"q": "old"})
                try:
                    self.assertTrue(started.wait(1))
                    newest = executor.submit(_suggestions_request, {"q": "new"})
                    self.assertEqual(newest.result(timeout=1)["query"], "new")
                finally:
                    release.set()
                    first.result(timeout=2)

    @patch("trips.services.routing.geocoding._geocoding_request")
    def test_fuzzy_provider_cannot_silently_change_requested_state(self, request):
        request.return_value = [
            {
                "display_name": "Madison, Alabama",
                "lon": -86.75,
                "lat": 34.7,
                "address": {"state": "Alabama", "country_code": "us"},
            }
        ]
        with self.assertRaisesRegex(LocationError, "Wisconsin"):
            geocode("Madison, WI")

    @patch("trips.services.routing.geocoding._geocoding_request")
    def test_numbered_address_cannot_fall_back_to_city_centroid(self, request):
        request.return_value = [
            {
                "display_name": "Madison, Wisconsin",
                "lon": -89.4,
                "lat": 43.07,
                "address": {"state": "Wisconsin", "country_code": "us"},
            }
        ]
        with self.assertRaisesRegex(LocationError, "street number"):
            geocode("123 Main Street, Madison, WI")

    def test_invalid_photon_coordinates_are_rejected(self):
        from trips.services.routing.photon import photon_results

        for coordinates in ([float("nan"), 42], [-181, 42], [-90, 91], [-90]):
            with self.subTest(coordinates=coordinates), self.assertRaises(RoutingError):
                photon_results(
                    {"features": [photon_place("Bad data", "United States", "US", coordinates)]}
                )

    @patch("trips.services.routing.geocoding._geocoding_request")
    def test_malformed_compatible_geocoder_response_is_controlled(self, request):
        for result in (
            None,
            {"display_name": "Bad", "address": None},
            {"display_name": "Bad", "address": {"ISO3166-2-lvl4": 12}},
        ):
            with self.subTest(result=result), self.assertRaises(RoutingError):
                request.return_value = [result]
                geocode("Madison, WI")
