from datetime import datetime, timedelta, timezone
from unittest import TestCase

from trips.services.hos import HOUR, Leg, plan_schedule
from trips.services.logs import daily_logs

from .test_hos import SchedulingTests

START = datetime(2026, 10, 3, 8, tzinfo=timezone(timedelta(hours=-6)))


class InspectionTests(TestCase):
    def plan(self, hours=3, cycle=0, start=START):
        return plan_schedule(
            [Leg(55, HOUR, "Pickup"), Leg(hours * 55, hours * HOUR, "Dropoff")],
            start,
            cycle,
            "Start",
        )

    def test_inspections_count_as_on_duty_work_in_logs(self):
        events = self.plan()
        inspections = [e for e in events if "inspection / TIV" in e["activity"]]
        self.assertEqual(len(inspections), 2)
        self.assertTrue(
            all(e["status"] == "on_duty" and e["duration_seconds"] == 900 for e in inspections)
        )
        logs = daily_logs(events)
        self.assertEqual(sum(log["totals_minutes"]["on_duty"] for log in logs), 150)
        self.assertTrue(
            any(
                "Pre-trip inspection / TIV" in r["activity"] for log in logs for r in log["remarks"]
            )
        )
        self.assertTrue(
            any(
                "Post-trip inspection / TIV" in r["activity"]
                for log in logs
                for r in log["remarks"]
            )
        )

    def test_new_driving_shift_gets_inspections_but_midnight_alone_does_not(self):
        events = self.plan(hours=14, start=START.replace(hour=20))
        inspected = False
        pre = post = rests = 0
        for event in events:
            if event["activity"].startswith("Pre-trip"):
                self.assertFalse(inspected)
                inspected = True
                pre += 1
            elif event["activity"].startswith("Post-trip"):
                self.assertTrue(inspected)
                inspected = False
                post += 1
            elif event["status"] == "driving":
                self.assertTrue(inspected)
            elif event["status"] == "sleeper_berth":
                self.assertFalse(inspected)
                rests += 1
        self.assertEqual(pre, post)
        self.assertEqual(pre, rests + 1)
        self.assertFalse(inspected)

    def test_near_full_cycle_stops_driving_and_restarts_safely(self):
        for cycle in (69.4, 69.5, 69.99, 70):
            with self.subTest(cycle=cycle):
                events = self.plan(cycle=cycle)
                SchedulingTests.assert_valid(self, events, cycle)
                self.assertTrue(any(e["activity"].startswith("Cycle restart") for e in events))

    def test_pre_trip_uses_the_fourteen_hour_window(self):
        events = self.plan(hours=20)
        SchedulingTests.assert_valid(self, events, 0)
        first_drive = next(e for e in events if e["status"] == "driving")
        self.assertEqual(first_drive["start"], (START + timedelta(minutes=15)).isoformat())
