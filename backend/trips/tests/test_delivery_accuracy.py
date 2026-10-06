"""Delivery regressions for independent clock, mileage and midnight invariants."""

import random
from datetime import timedelta
from unittest import TestCase

from trips.services.hos import HOUR, Leg, build_schedule
from trips.services.logs import daily_logs
from trips.services.routing import RouteLocator

from .test_hos import START, SchedulingTests


class DeliveryAccuracyTests(TestCase):
    def test_seeded_fractional_trips_preserve_clocks_mileage_and_log_coverage(self):
        # Reproducible integer-second cases include boundaries that whole-hour
        # fixtures miss. The oracle checks output invariants, not planner branches.
        rng = random.Random(20261006)
        boundaries = [0, 1, 8 * HOUR - 1, 8 * HOUR, 11 * HOUR, 14 * HOUR, 70 * HOUR]
        for case in range(180):
            durations = [
                rng.choice(boundaries) if case % 3 == 0 else rng.randrange(1, 90 * HOUR)
                for _ in range(2)
            ]
            initial_cycle = rng.choice([0, 20.125, 65.7, 69.7499, 69.9999, 70])
            legs = [
                Leg(seconds / HOUR * rng.uniform(25, 70), seconds, destination)
                for seconds, destination in zip(durations, ["Pickup", "Dropoff"])
            ]
            with self.subTest(case=case, durations=durations, cycle=initial_cycle):
                schedule = build_schedule(legs, START, initial_cycle, "Start")
                events = schedule.events
                SchedulingTests.assert_valid(self, events, initial_cycle)
                self.assertEqual(
                    sum(e["duration_seconds"] for e in events if e["status"] == "driving"),
                    sum(durations),
                )
                self.assertAlmostEqual(
                    sum(e["distance_miles"] for e in events),
                    sum(leg.distance_miles for leg in legs),
                )
                for activity in ("Pickup (1 hour)", "Drop-off (1 hour)"):
                    work = [e for e in events if e["activity"] == activity]
                    self.assertEqual(len(work), 1)
                    self.assertEqual(work[0]["duration_seconds"], HOUR)
                for log in daily_logs(events):
                    self.assertEqual(sum(log["totals_minutes"].values()), 1440)
                    self.assertTrue(all(value >= 0 for value in log["totals_minutes"].values()))

    def test_fueling_at_pickup_boundary_counts_as_work_and_satisfies_break(self):
        schedule = build_schedule(
            [Leg(1000, 20 * HOUR, "Pickup"), Leg(50, HOUR, "Dropoff")],
            START,
            0,
            "Start",
        )
        fuel = [event for event in schedule.events if event["activity"].startswith("Fueling")]
        self.assertEqual(len(fuel), 1)
        self.assertAlmostEqual(fuel[0]["start_route_miles"], 1000)
        self.assertEqual(fuel[0]["status"], "on_duty")
        self.assertEqual(fuel[0]["duration_seconds"], 30 * 60)
        SchedulingTests.assert_valid(self, schedule.events, 0)

    def test_reaching_eight_hours_at_destination_does_not_insert_useless_break(self):
        schedule = build_schedule(
            [Leg(0, 0, "Pickup"), Leg(440, 8 * HOUR, "Dropoff")], START, 0, "Start"
        )
        self.assertFalse(any(e["activity"].startswith("Driving break") for e in schedule.events))
        SchedulingTests.assert_valid(self, schedule.events, 0)

    def test_exact_midnight_completion_does_not_create_empty_following_sheet(self):
        # Two 1h drives, two 1h work stops and two 15m inspections end at 24:00.
        departure = START.replace(hour=19, minute=30)
        schedule = build_schedule(
            [Leg(55, HOUR, "Pickup"), Leg(55, HOUR, "Dropoff")], departure, 0, "Start"
        )
        logs = daily_logs(schedule.events)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["segments"][-1]["end_minute"], 1440)
        self.assertEqual(sum(logs[0]["totals_minutes"].values()), 1440)
        self.assertNotEqual(logs[0]["remarks"][-1]["activity"], "Trip complete; off duty")

    def test_midnight_continuation_resolves_its_new_road_and_preserves_mileage(self):
        midnight = START.replace(hour=0) + timedelta(days=1)
        event = {
            "start": (midnight - timedelta(hours=2)).isoformat(),
            "end": (midnight + timedelta(hours=2)).isoformat(),
            "duration_seconds": 4 * HOUR,
            "distance_miles": 200,
            "start_route_miles": 0,
            "status": "driving",
            "activity": "Drive to destination",
            "location": "Starting city",
            "road": "Old road",
            "coordinates": [0, 0],
        }
        locator = RouteLocator(
            [
                {
                    "distance_miles": 200,
                    "geometry": {"coordinates": [[0, 0], [1, 0], [1, 1]]},
                    "instructions": [
                        {"distance_miles": 80, "road": "Old road"},
                        {"distance_miles": 120, "road": "Current road"},
                    ],
                }
            ]
        )
        logs = daily_logs([event], position_at=locator.at, road_at=locator.road_at)
        continued = logs[1]["activities"][0]
        self.assertEqual(continued["road"], "Current road")
        self.assertEqual(logs[1]["remarks"][0]["road"], "Current road")
        self.assertEqual(continued["coordinates"], [1, 0])
        self.assertEqual(sum(log["distance_miles"] for log in logs), 200)
        self.assertEqual(logs[0]["remarks"][1]["road"], "Old road")

        # A caller without road data must not print the event's old starting road.
        without_roads = daily_logs([event], position_at=locator.at)
        self.assertIsNone(without_roads[1]["remarks"][0]["road"])
        without_locator = daily_logs([event])
        self.assertIsNone(without_locator[1]["remarks"][0]["road"])
        self.assertIn("position not supplied", without_locator[1]["remarks"][0]["location"])
