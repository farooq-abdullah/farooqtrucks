from datetime import datetime, timedelta, timezone
from unittest import TestCase

from trips.services.hos import HOUR, Leg, plan_schedule
from trips.services.logs import daily_logs

START = datetime(2026, 10, 3, 8, tzinfo=timezone(timedelta(hours=-6)))


class SchedulingTests(TestCase):
    def plan(self, first_hours=0, second_hours=2, cycle=0, first_miles=None, second_miles=None):
        return plan_schedule(
            [
                Leg(
                    first_miles if first_miles is not None else first_hours * 55,
                    round(first_hours * HOUR),
                    "Pickup City, IL",
                ),
                Leg(
                    second_miles if second_miles is not None else second_hours * 55,
                    round(second_hours * HOUR),
                    "Dropoff City, TX",
                ),
            ],
            START,
            cycle,
            "Start City, IL",
        )

    def assert_valid(self, events, initial_cycle):
        cycle = round(initial_cycle * HOUR)
        driving = 0
        since_break = 0
        non_driving = 0
        rest = 0
        shift_start = START
        fuel_miles = 0
        previous_end = START
        for event in events:
            start = datetime.fromisoformat(event["start"])
            end = datetime.fromisoformat(event["end"])
            seconds = event["duration_seconds"]
            self.assertEqual(start, previous_end)
            self.assertEqual((end - start).total_seconds(), seconds)
            self.assertGreater(seconds, 0)
            previous_end = end
            if event["status"] == "driving":
                driving += seconds
                since_break += seconds
                cycle += seconds
                fuel_miles += event["distance_miles"]
                self.assertLessEqual(driving, 11 * HOUR)
                self.assertLessEqual(since_break, 8 * HOUR)
                self.assertLessEqual((end - shift_start).total_seconds(), 14 * HOUR)
                self.assertLessEqual(cycle, 70 * HOUR)
                self.assertLessEqual(fuel_miles, 1000 + 1e-6)
                non_driving = rest = 0
            else:
                non_driving += seconds
                if event["status"] == "on_duty":
                    cycle += seconds
                    rest = 0
                else:
                    rest += seconds
                if non_driving >= 1800:
                    since_break = 0
                if rest >= 10 * HOUR:
                    driving = 0
                    shift_start = end
                if rest >= 34 * HOUR:
                    cycle = 0
                if event["activity"].startswith("Fueling"):
                    fuel_miles = 0
        logs = daily_logs(events)
        for log in logs:
            self.assertAlmostEqual(log["total_hours"], 24)
            self.assertEqual(log["segments"][0]["start_minute"], 0)
            self.assertEqual(log["segments"][-1]["end_minute"], 1440)
            for left, right in zip(log["segments"], log["segments"][1:]):
                self.assertEqual(left["end_minute"], right["start_minute"])
        self.assertAlmostEqual(
            sum(log["distance_miles"] for log in logs),
            sum(event["distance_miles"] for event in events),
        )

    def test_short_trip_has_two_one_hour_work_stops(self):
        events = self.plan(1, 2)
        self.assertEqual(sum(e["duration_seconds"] for e in events), 5.5 * HOUR)
        self.assertEqual(
            [e["activity"] for e in events if e["status"] == "on_duty"],
            [
                "Pre-trip inspection / TIV (15 minutes)",
                "Pickup (1 hour)",
                "Drop-off (1 hour)",
                "Post-trip inspection / TIV (15 minutes)",
            ],
        )
        self.assert_valid(events, 0)

    def test_eight_hour_limit_inserts_break_before_more_driving(self):
        events = self.plan(0, 9)
        self.assertEqual(
            [e["duration_seconds"] for e in events if e["status"] == "off_duty"], [1800]
        )
        self.assert_valid(events, 0)

    def test_loading_satisfies_driving_break(self):
        events = self.plan(8, 2)
        self.assertFalse(any(e["status"] == "off_duty" for e in events))
        self.assert_valid(events, 0)

    def test_daily_driving_restarts_only_after_ten_hour_rest(self):
        events = self.plan(0, 12)
        self.assertEqual(sum(e["activity"].startswith("Daily rest") for e in events), 1)
        self.assert_valid(events, 0)

    def test_seventy_used_hours_restarts_before_driving(self):
        events = self.plan(1, 1, cycle=70)
        self.assertEqual(events[0]["activity"], "Cycle restart (34 hours)")
        self.assertEqual(events[0]["duration_seconds"], 34 * HOUR)
        self.assert_valid(events, 70)

    def test_cycle_includes_loading_and_fueling(self):
        events = self.plan(1, 1, cycle=68.5)
        self.assertTrue(any(e["activity"] == "Cycle restart (34 hours)" for e in events))
        self.assert_valid(events, 68.5)

    def test_fuel_stop_at_or_before_every_thousand_miles(self):
        events = self.plan(0, 45, second_miles=2300)
        fueling = [e for e in events if e["activity"].startswith("Fueling")]
        self.assertEqual(len(fueling), 2)
        self.assertLessEqual(fueling[0]["start_route_miles"], 1000)
        self.assertLessEqual(
            fueling[1]["start_route_miles"] - fueling[0]["start_route_miles"], 1000
        )
        self.assert_valid(events, 0)

    def test_midnight_split_preserves_mileage_and_twenty_four_hours(self):
        events = self.plan(0, 16)
        self.assertGreater(len(daily_logs(events)), 1)
        self.assert_valid(events, 0)

    def test_final_off_duty_transition_has_a_remark(self):
        events = self.plan(1, 2)
        log = daily_logs(events)[0]
        self.assertEqual(log["remarks"][-1]["activity"], "Trip complete; off duty")
        self.assertEqual(log["remarks"][-1]["time"], "13:30:00")

    def test_midnight_continuation_has_a_remark(self):
        logs = daily_logs(self.plan(1, 1, cycle=70))
        self.assertEqual(logs[1]["remarks"][0]["time"], "00:00:00")
        self.assertTrue(logs[1]["remarks"][0]["activity"].startswith("Continue"))

    def test_zero_distance_locations_still_have_pickup_and_dropoff(self):
        events = self.plan(0, 0)
        self.assertEqual(len(events), 2)
        self.assert_valid(events, 0)

    def test_many_trip_lengths_and_starting_cycles_stay_within_limits(self):
        # A sweep checks combinations and fractional cycle values rather than
        # duplicating the scheduler's branching implementation.
        for first in (0, 3, 8, 11, 18):
            for second in (0, 0.1, 7.9, 11, 30, 100):
                for cycle in (0, 25.5, 65, 69.999, 70):
                    with self.subTest(first=first, second=second, cycle=cycle):
                        self.assert_valid(self.plan(first, second, cycle), cycle)

    def test_fourteen_hour_window_is_elapsed_time_including_non_driving(self):
        # Exercise a day with non-driving work that uses the window before the
        # 11 driving hours are exhausted.
        from trips.services.hos import Planner

        planner = Planner(START, 0, "Start")
        planner.work(4 * HOUR, "Loading delay", "Start")
        planner.drive(Leg(550, 10 * HOUR, "Destination"), 0)
        planner.work(HOUR, "Drop-off", "Destination")
        self.assertTrue(any(e["activity"].startswith("Daily rest") for e in planner.events))
        self.assert_valid(planner.events, 0)
