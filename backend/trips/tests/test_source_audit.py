"""Independent examples and boundary regressions from the complete source audit."""

from datetime import timedelta
from unittest import TestCase
from unittest.mock import patch

from django.core.cache import cache

from trips.services.hos import HOUR, Leg, Planner, build_schedule
from trips.services.logs import daily_logs
from trips.services.routing import RouteLocator, annotate_schedule, geocode

from .test_api import LOCATIONS, example_route
from .test_hos import START, SchedulingTests


class SourceAuditTests(TestCase):
    def test_activity_details_keep_adjacent_work_separate(self):
        schedule = build_schedule(
            [Leg(55, HOUR, "Pickup"), Leg(55, HOUR, "Dropoff")], START, 0, "Start"
        )
        log = daily_logs(schedule.events)[0]
        final_work = next(
            segment for segment in reversed(log["segments"]) if segment["status"] == "on_duty"
        )
        self.assertEqual(final_work["end_minute"] - final_work["start_minute"], 75)
        activities = [activity for activity in log["activities"] if activity["status"] == "on_duty"]
        self.assertEqual(
            [activity["activity"] for activity in activities[-2:]],
            ["Drop-off (1 hour)", "Post-trip inspection / TIV (15 minutes)"],
        )
        self.assertEqual(activities[-1]["end_minute"] - activities[-1]["start_minute"], 15)
        self.assertIn("planning estimate", activities[-1]["reason"])

    def test_rest_details_keep_full_interval_across_midnight(self):
        schedule = build_schedule(
            [Leg(660, 12 * HOUR, "Pickup"), Leg(55, HOUR, "Dropoff")], START, 20, "Start"
        )
        logs = daily_logs(schedule.events)
        first_rest = next(a for a in logs[0]["activities"] if a["status"] == "sleeper_berth")
        continued = logs[1]["activities"][0]
        self.assertIn("11-hour driving limit", first_rest["reason"])
        self.assertEqual(
            (first_rest["end_minute"] - first_rest["start_minute"])
            + (continued["end_minute"] - continued["start_minute"]),
            10 * 60,
        )
        self.assertEqual(first_rest["event_start"], continued["event_start"])
        self.assertEqual(first_rest["event_end"], continued["event_end"])
        delayed = Planner(START, 0, "Start")
        delayed.work(4 * HOUR, "Loading delay", "Start")
        delayed.drive(Leg(550, 10 * HOUR, "Destination"), 0)
        rest = next(event for event in delayed.events if event["activity"].startswith("Daily rest"))
        self.assertIn("14-hour driving window", rest["reason"])

    @patch(
        "trips.services.routing.geocoding._geocoding_request",
        return_value=[
            {
                "display_name": "123 Main Street, Springfield, Illinois, United States",
                "lon": "-89.65",
                "lat": "39.78",
                "address": {
                    "city": "Springfield",
                    "state": "Illinois",
                    "ISO3166-2-lvl4": "US-IL",
                    "country_code": "us",
                },
            }
        ],
    )
    def test_address_input_uses_city_and_state_in_log_remarks(self, request):
        cache.clear()
        location = geocode("123 Main Street, Springfield, IL")
        self.assertEqual(location["log_location"], "Springfield, IL")
        self.assertIn("123 Main Street", location["label"])
        event = {
            "start_route_miles": 200,
            "end_route_miles": 200,
            "status": "on_duty",
            "location": location["label"],
        }
        annotate_schedule([event], example_route(), [location])
        self.assertEqual(event["location"], "Springfield, IL")

    def test_fmcsa_page_nineteen_grid_totals(self):
        # Guide pp.18–19, Richmond to Newark. Includes non-driving work beyond
        # the 14-hour driving window; this is permitted in the source example.
        spans = [
            (0, 6, "off_duty"),
            (6, 7.5, "on_duty"),
            (7.5, 9, "driving"),
            (9, 9.5, "on_duty"),
            (9.5, 12, "driving"),
            (12, 13, "off_duty"),
            (13, 15, "driving"),
            (15, 15.5, "on_duty"),
            (15.5, 16, "driving"),
            (16, 17.75, "sleeper_berth"),
            (17.75, 19, "driving"),
            (19, 21, "on_duty"),
            (21, 24, "off_duty"),
        ]
        midnight = START.replace(hour=0)
        events = [
            {
                "start": (midnight + timedelta(hours=a)).isoformat(),
                "end": (midnight + timedelta(hours=b)).isoformat(),
                "status": status,
                "activity": "Source example",
                "location": "Example city, VA",
                "duration_seconds": (b - a) * HOUR,
                "distance_miles": 0,
            }
            for a, b, status in spans
        ]
        log = daily_logs(events)[0]
        self.assertEqual(
            log["totals_hours"],
            {"off_duty": 10, "sleeper_berth": 1.75, "driving": 7.75, "on_duty": 4.5},
        )
        self.assertEqual(sum(log["totals_minutes"].values()), 1440)

    def test_unloading_and_post_trip_can_finish_above_seventy(self):
        schedule = build_schedule(
            [Leg(55, HOUR, "Pickup"), Leg(55, HOUR, "Dropoff")], START, 66, "Start"
        )
        self.assertFalse(any(e["activity"].startswith("Cycle restart") for e in schedule.events))
        self.assertEqual(schedule.cycle / HOUR, 70.5)
        self.assertEqual(schedule.events[-1]["status"], "on_duty")
        SchedulingTests.assert_valid(self, schedule.events, 66)

    def test_loading_above_seventy_requires_restart_before_next_drive(self):
        schedule = build_schedule(
            [Leg(55, HOUR, "Pickup"), Leg(55, HOUR, "Dropoff")], START, 68.5, "Start"
        )
        pickup = next(
            i for i, e in enumerate(schedule.events) if e["activity"].startswith("Pickup")
        )
        restart = next(
            i for i, e in enumerate(schedule.events) if e["activity"].startswith("Cycle restart")
        )
        self.assertLess(pickup, restart)
        SchedulingTests.assert_valid(self, schedule.events, 68.5)

    def test_stationary_work_at_full_cycle_needs_no_driving_restart(self):
        schedule = build_schedule([Leg(0, 0, "Pickup"), Leg(0, 0, "Dropoff")], START, 70, "Start")
        self.assertEqual(len(schedule.events), 2)
        self.assertEqual(schedule.cycle / HOUR, 72)
        self.assertTrue(all(e["status"] == "on_duty" for e in schedule.events))

    def test_consecutive_mixed_nondriving_periods_satisfy_break(self):
        planner = Planner(START, 0, "Start")
        planner.drive(Leg(440, 8 * HOUR, "Stop"), 0)
        planner.work(15 * 60, "Paperwork", "Stop")
        planner._emit(15 * 60, "off_duty", "Personal break")
        planner.drive(Leg(55, HOUR, "Destination"), 1)
        self.assertFalse(any(e["activity"].startswith("Driving break") for e in planner.events))
        SchedulingTests.assert_valid(self, planner.events, 0)

    def test_non_driving_work_after_fourteen_does_not_reset_cycle(self):
        planner = Planner(START, 20, "Start")
        planner.drive(Leg(55, HOUR, "Stop"), 0)
        planner.work(14 * HOUR, "Loading delay", "Stop")
        planner.drive(Leg(55, HOUR, "Destination"), 1)
        self.assertTrue(any(e["activity"].startswith("Daily rest") for e in planner.events))
        self.assertFalse(any(e["activity"].startswith("Cycle restart") for e in planner.events))
        self.assertGreater(planner.cycle / HOUR, 36)
        SchedulingTests.assert_valid(self, planner.events, 20)

    def test_midnight_driving_continuation_uses_polyline_position(self):
        midnight = START.replace(hour=0) + timedelta(days=1)
        event = {
            "start": (midnight - timedelta(hours=2)).isoformat(),
            "end": (midnight + timedelta(hours=2)).isoformat(),
            "status": "driving",
            "activity": "Drive to Destination",
            "location": "Old town, IL",
            "coordinates": [0, 0],
            "end_coordinates": [1, 1],
            "duration_seconds": 4 * HOUR,
            "distance_miles": 100,
            "start_route_miles": 0,
        }
        locator = RouteLocator(
            [{"distance_miles": 100, "geometry": {"coordinates": [[0, 0], [1, 0], [1, 1]]}}]
        )
        logs = daily_logs([event], position_at=locator.at)
        remark = logs[1]["remarks"][0]
        self.assertEqual(remark["coordinates"], [1, 0])
        self.assertIn("In transit", remark["location"])
        self.assertNotIn("Old town", remark["location"])
        self.assertEqual(sum(log["distance_miles"] for log in logs), 100)

    @patch("trips.services.routing.locations.reverse_label", return_value="Near Springfield, IL")
    def test_road_context_survives_in_location_remarks(self, reverse):
        route = example_route()
        route["legs"][0]["instructions"] = [
            {"distance_miles": 100, "road": "I 55"},
            {"distance_miles": 100, "road": "US 66"},
        ]
        event = {
            "start": START.isoformat(),
            "end": (START + timedelta(minutes=30)).isoformat(),
            "status": "off_duty",
            "activity": "Driving break",
            "location": "Along route",
            "duration_seconds": 1800,
            "distance_miles": 0,
            "start_route_miles": 150,
            "end_route_miles": 150,
        }
        annotate_schedule([event], route, LOCATIONS)
        self.assertEqual(event["road"], "US 66")
        self.assertEqual(daily_logs([event])[0]["remarks"][1]["road"], "US 66")
