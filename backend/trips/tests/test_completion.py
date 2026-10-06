from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.test import SimpleTestCase
from rest_framework.test import APIClient

from trips.services.hos import HOUR, Leg, build_schedule, completion_clocks
from trips.services.logs import daily_logs

from .test_api import INPUTS, LOCATIONS, example_route

START = datetime(2026, 10, 3, 8, tzinfo=timezone(timedelta(hours=-6)))


class CompletionTests(TestCase):
    def test_final_clocks_come_from_current_shift_after_restart(self):
        schedule = build_schedule(
            [Leg(55, HOUR, "Pickup"), Leg(55, HOUR, "Dropoff")], START, 70, "Start"
        )
        clocks = completion_clocks(schedule)
        self.assertEqual(clocks["cycle_used_hours"], 4.5)
        self.assertEqual(clocks["cycle_remaining_hours"], 65.5)
        self.assertEqual(clocks["driving_used_hours"], 2)
        self.assertEqual(clocks["shift_used_hours"], 4.5)
        self.assertEqual(clocks["break_driving_hours"], 0)

    def test_printed_minutes_sum_to_twenty_four_even_at_half_minute(self):
        schedule = build_schedule(
            [Leg(20, 1800, "Pickup"), Leg(20, 1830, "Dropoff")], START, 0, "Start"
        )
        log = daily_logs(schedule.events)[0]
        self.assertEqual(sum(log["totals_minutes"].values()), 1440)
        self.assertAlmostEqual(log["total_hours"], 24)


class DeploymentAndContractTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_health_checks_do_not_exhaust_trip_throttle(self):
        for _ in range(35):
            self.assertEqual(self.client.get("/api/health/").status_code, 200)

    @patch("trips.views.annotate_schedule", return_value=[])
    @patch("trips.views.road_route", side_effect=lambda locations: example_route())
    @patch("trips.views.geocode", side_effect=LOCATIONS)
    def test_unloading_and_post_trip_do_not_require_restart_after_arrival(
        self, geocode, route, annotate
    ):
        departure = datetime(2026, 10, 3, 8, tzinfo=ZoneInfo("America/Chicago"))
        with patch("trips.views.default_departure", return_value=departure):
            response = self.client.post(
                "/api/trips/plan/", {**INPUTS, "current_cycle_used": 62.5}, format="json"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["arrival_time"], "2026-10-03T15:15:00-05:00")
        self.assertEqual(response.data["summary"]["completion_time"], "2026-10-03T16:30:00-05:00")
        self.assertEqual(response.data["summary"]["cycle_restarts"], 0)
        self.assertEqual(response.data["clocks"]["cycle_used_hours"], 71)
        self.assertEqual(response.data["clocks"]["cycle_remaining_hours"], 0)
        self.assertTrue(
            all(sum(log["totals_minutes"].values()) == 1440 for log in response.data["daily_logs"])
        )
