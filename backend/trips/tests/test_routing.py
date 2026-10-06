"""Reject malformed upstream routes before they reach clocks, logs or the map."""

from copy import deepcopy
from unittest.mock import patch

import requests
from django.core.cache import cache
from django.test import SimpleTestCase
from rest_framework.test import APIClient

from trips.services.hos import Leg, build_schedule
from trips.services.logs import daily_logs
from trips.services.routing import RouteLocator, RoutingError, road_route
from trips.services.routing import client as routing_client
from trips.services.routing.routes import MAX_DRIVING_SECONDS, METERS_PER_MILE

from .test_api import INPUTS, LOCATIONS
from .test_hos import START


def provider_route():
    legs = []
    for first, last in zip(LOCATIONS, LOCATIONS[1:]):
        points = [first["coordinates"], last["coordinates"]]
        legs.append(
            {
                "distance": 1000.0,
                "duration": 60.1,
                "steps": [
                    {
                        "geometry": {"type": "LineString", "coordinates": deepcopy(points)},
                        "maneuver": {"type": "depart", "location": points[0][:]},
                        "name": "Main Street",
                        "ref": "US 1",
                        "distance": 1000.0,
                        "duration": 60.1,
                    }
                ],
            }
        )
    return {
        "code": "Ok",
        "routes": [
            {
                "legs": legs,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [p["coordinates"] for p in LOCATIONS],
                },
            }
        ],
    }


class RoutingContractTests(SimpleTestCase):
    def route(self, data):
        with patch("trips.services.routing.routes._request", return_value=data):
            return road_route(LOCATIONS)

    def test_valid_route_preserves_distance_and_rounds_seconds_conservatively(self):
        result = self.route(provider_route())
        self.assertAlmostEqual(result["distance_miles"], 2000 / METERS_PER_MILE)
        self.assertEqual(result["driving_seconds"], 122)
        self.assertEqual(result["legs"][0]["instructions"][0]["road"], "US 1 · Main Street")
        locator = RouteLocator(result["legs"])
        self.assertEqual(locator.at(0), LOCATIONS[0]["coordinates"])
        self.assertEqual(locator.at(result["distance_miles"]), LOCATIONS[-1]["coordinates"])

    def test_invalid_step_and_leg_numbers_raise_provider_error(self):
        for level in ("leg", "step"):
            for field in ("distance", "duration"):
                for value in (float("inf"), float("nan"), -1, True, "12", None, {}):
                    with self.subTest(level=level, field=field, value=value):
                        data = provider_route()
                        target = data["routes"][0]["legs"][0]
                        if level == "step":
                            target = target["steps"][0]
                        target[field] = value
                        with self.assertRaises(RoutingError):
                            self.route(data)

    def test_invalid_geometry_and_maneuver_coordinates_raise_provider_error(self):
        for target in ("overview", "step", "maneuver"):
            for point in (
                [],
                [0],
                [0, 0, 0],
                ["bad", 40],
                [False, 40],
                [float("nan"), 40],
                [-89, float("inf")],
                [181, 40],
                [-89, -91],
            ):
                with self.subTest(target=target, point=point):
                    data = provider_route()
                    source = data["routes"][0]
                    step = source["legs"][0]["steps"][0]
                    if target == "maneuver":
                        step["maneuver"]["location"] = point
                    else:
                        geometry = source["geometry"] if target == "overview" else step["geometry"]
                        geometry["coordinates"][0] = point
                    with self.assertRaises(RoutingError):
                        self.route(data)

    def test_invalid_maneuver_text_cannot_escape_as_attribute_error(self):
        for field in ("type", "modifier"):
            for value in (None, 4, [], {}):
                with self.subTest(field=field, value=value):
                    data = provider_route()
                    data["routes"][0]["legs"][0]["steps"][0]["maneuver"][field] = value
                    with self.assertRaises(RoutingError):
                        self.route(data)

    def test_missing_or_wrong_shape_route_geometry_is_rejected(self):
        for geometry in (
            {},
            None,
            {"type": "Polygon", "coordinates": [[-89, 40]]},
            {"type": "LineString", "coordinates": []},
        ):
            with self.subTest(geometry=geometry):
                data = provider_route()
                data["routes"][0]["geometry"] = geometry
                with self.assertRaises(RoutingError):
                    self.route(data)

    def test_moving_leg_cannot_be_represented_by_only_one_position(self):
        data = provider_route()
        data["routes"][0]["legs"][0]["steps"][0]["geometry"]["coordinates"] = [[-89, 40]]
        with self.assertRaises(RoutingError):
            self.route(data)

    def test_zero_distance_single_position_routes_keep_pickup_and_dropoff(self):
        data = provider_route()
        position = LOCATIONS[0]["coordinates"]
        source = data["routes"][0]
        source["geometry"]["coordinates"] = [position]
        for leg in source["legs"]:
            leg.update(distance=0, duration=0)
            step = leg["steps"][0]
            step.update(distance=0, duration=0)
            step["geometry"]["coordinates"] = [position]
            step["maneuver"]["location"] = position
        result = self.route(data)
        self.assertEqual(result["distance_miles"], 0)
        self.assertEqual(result["driving_seconds"], 0)
        self.assertEqual(RouteLocator(result["legs"]).at(0), position)
        self.assertEqual(result["geometry"]["coordinates"], [position, position])
        schedule = build_schedule(
            [
                Leg(leg["distance_miles"], leg["duration_seconds"], "Same location")
                for leg in result["legs"]
            ],
            START,
            0,
            "Same location",
        )
        self.assertEqual(
            [e["activity"] for e in schedule.events], ["Pickup (1 hour)", "Drop-off (1 hour)"]
        )
        self.assertEqual(daily_logs(schedule.events)[0]["total_hours"], 24)

    def test_moving_leg_rounded_to_zero_seconds_still_gets_one_second(self):
        data = provider_route()
        for leg in data["routes"][0]["legs"]:
            leg["distance"] = 0.25  # A sub-meter movement can round to zero seconds.
            leg["duration"] = 0
            leg["steps"][0]["distance"] = 0.25
            leg["steps"][0]["duration"] = 0
        result = self.route(data)
        self.assertEqual(result["driving_seconds"], 2)

    def test_impossible_provider_speed_is_rejected_before_fueling_can_loop(self):
        data = provider_route()
        leg = data["routes"][0]["legs"][0]
        leg.update(distance=1001 * METERS_PER_MILE, duration=1)
        leg["steps"][0].update(distance=leg["distance"], duration=1)
        with self.assertRaises(RoutingError):
            self.route(data)

    def test_total_duration_is_bounded_before_scheduling(self):
        data = provider_route()
        for leg in data["routes"][0]["legs"]:
            leg["duration"] = MAX_DRIVING_SECONDS / 2 + 1
            leg["steps"][0]["duration"] = leg["duration"]
        with self.assertRaisesRegex(RoutingError, "implausible driving duration"):
            self.route(data)

    def test_incomplete_and_no_route_responses_remain_provider_errors(self):
        for data in (None, [], {}, {"code": "NoRoute"}, {"code": "Ok", "routes": [{}]}):
            with self.subTest(data=data):
                with self.assertRaises(RoutingError):
                    self.route(data)

    @patch("trips.views.geocode", side_effect=LOCATIONS)
    def test_corrupt_provider_response_returns_502_without_scheduling(self, geocode):
        cache.clear()
        data = provider_route()
        data["routes"][0]["legs"][0]["steps"][0]["duration"] = float("inf")
        with (
            patch("trips.services.routing.routes._request", return_value=data),
            patch("trips.views.build_schedule") as schedule,
        ):
            response = APIClient().post("/api/trips/plan/", INPUTS, format="json")
        self.assertEqual(response.status_code, 502)
        self.assertIn("routing service", response.data["detail"])
        schedule.assert_not_called()


class RoutingTransportRetryTests(SimpleTestCase):
    def setUp(self):
        session_patch = patch.object(routing_client._http, "session", create=True)
        self.session = session_patch.start()
        self.addCleanup(session_patch.stop)

    def response(self, status, data=None):
        response = requests.Response()
        response.status_code = status
        response._content = b"{}"
        response.json = lambda: data
        return response

    def test_road_route_retries_one_transient_service_unavailable(self):
        self.session.get.side_effect = [
            self.response(503),
            self.response(200, provider_route()),
        ]
        with patch.object(routing_client.time, "sleep") as sleep:
            result = road_route(LOCATIONS)
        self.assertEqual(result["provider"], "OSRM")
        self.assertEqual(self.session.get.call_count, 2)
        sleep.assert_called_once()
        self.assertLessEqual(sleep.call_args.args[0], 0.2)

    def test_two_transient_failures_return_bounded_readable_routing_error(self):
        self.session.get.side_effect = [self.response(503), self.response(503)]
        with patch.object(routing_client.time, "sleep") as sleep:
            with self.assertRaisesRegex(RoutingError, "map service is unavailable"):
                road_route(LOCATIONS)
        self.assertEqual(self.session.get.call_count, 2)
        sleep.assert_called_once()
        self.assertLessEqual(sleep.call_args.args[0], 0.2)

    def test_road_route_retries_transient_connection_failure(self):
        self.session.get.side_effect = [
            requests.ConnectionError("reset"),
            self.response(200, provider_route()),
        ]
        with patch.object(routing_client.time, "sleep"):
            self.assertEqual(road_route(LOCATIONS)["provider"], "OSRM")
        self.assertEqual(self.session.get.call_count, 2)
