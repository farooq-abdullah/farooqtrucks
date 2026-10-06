"""The driver's changing clocks and the operations that update them.

Keep the related methods together: each operation modifies the same Planner
state. This calculation layer has no Django, HTTP, maps or database dependency.
"""

import math
from datetime import datetime, timedelta

from .rules import (
    BREAK_LIMIT,
    CYCLE_LIMIT,
    DRIVE_LIMIT,
    FUEL_INTERVAL_MILES,
    HOUR,
    INSPECTION_SECONDS,
    WINDOW_LIMIT,
    Leg,
)


class Planner:
    def __init__(self, departure: datetime, cycle_used: float, current_location: str):
        self.departure = departure
        self.now = 0
        self.shift_start = 0
        self.shift_driving = 0
        self.driving_since_break = 0
        self.non_driving = 0
        self.cycle = math.ceil(cycle_used * HOUR)
        self.route_miles = 0.0
        self.fuel_miles = 0.0
        self.location = current_location
        self.events = []
        self.shift_inspected = False
        self.shift_drove = False

    def _emit(self, seconds, status, activity, miles=0.0, location=None, reason=None):
        if seconds <= 0:
            raise ValueError("An event must have positive duration.")
        start = self.now
        start_miles = self.route_miles
        self.now += seconds
        self.route_miles += miles
        if status == "driving":
            self.shift_drove = True
            self.cycle += seconds
            self.shift_driving += seconds
            self.driving_since_break += seconds
            self.fuel_miles += miles
            self.non_driving = 0
        else:
            self.non_driving += seconds
            if status == "on_duty":
                self.cycle += seconds
            if self.non_driving >= 30 * 60:
                self.driving_since_break = 0
        self.events.append(
            {
                "status": status,
                "activity": activity,
                "start": (self.departure + timedelta(seconds=start)).isoformat(),
                "end": (self.departure + timedelta(seconds=self.now)).isoformat(),
                "duration_seconds": seconds,
                "start_route_miles": start_miles,
                "end_route_miles": self.route_miles,
                "distance_miles": miles,
                "location": location or self.location,
                "reason": reason,
            }
        )

    def finish_shift(self):
        if self.shift_drove:
            self._emit(
                INSPECTION_SECONDS,
                "on_duty",
                "Post-trip inspection / TIV (15 minutes)",
                reason="Vehicle and trailer inspection before a full rest or trip completion. The 15-minute duration is a planning estimate.",
            )
            self.shift_drove = False

    def _rest(self, restart=False, reason=None):
        self.finish_shift()
        # Non-driving work can exceed the cycle limit. Restore capacity only
        # when the next pre-trip inspection would leave no time for driving.
        restart = restart or self.cycle + INSPECTION_SECONDS >= CYCLE_LIMIT
        if restart:
            reason = (
                "Not enough cycle hours remain for the next inspection and further driving. "
                "This plan uses a 34-hour restart because earlier daily hours for recapture were not supplied."
            )
        self._emit(
            34 * HOUR if restart else 10 * HOUR,
            "sleeper_berth",
            "Cycle restart (34 hours)" if restart else "Daily rest (10 hours)",
            reason=reason or "A full 10-hour rest starts fresh daily driving and shift clocks.",
        )
        self.shift_start = self.now
        self.shift_driving = 0
        self.driving_since_break = 0
        self.shift_inspected = False
        self.shift_drove = False
        if restart:
            self.cycle = 0

    def work(self, seconds, activity, location):
        # The 14-hour and 70-hour limits prohibit further driving, not work.
        # Finish loading/unloading now; drive() checks capacity before moving.
        self.location = location
        self._emit(seconds, "on_duty", activity, location=location)

    def drive(self, leg: Leg, leg_index: int):
        if leg.duration_seconds <= 0 or leg.distance_miles <= 0:
            self.location = leg.destination
            return
        remaining = leg.duration_seconds
        miles_per_second = leg.distance_miles / leg.duration_seconds
        while remaining > 0:
            if self.cycle >= CYCLE_LIMIT:
                self._rest(restart=True)
                continue
            if self.shift_driving >= DRIVE_LIMIT or self.now - self.shift_start >= WINDOW_LIMIT:
                reason = (
                    "The 11-hour driving limit was reached. A 10-hour rest starts fresh daily clocks."
                    if self.shift_driving >= DRIVE_LIMIT
                    else "The 14-hour driving window was reached. A 10-hour rest starts a new driving window."
                )
                self._rest(reason=reason)
                continue
            if not self.shift_inspected:
                if self.cycle + INSPECTION_SECONDS >= CYCLE_LIMIT:
                    self._rest(restart=True)
                    continue
                self._emit(
                    INSPECTION_SECONDS,
                    "on_duty",
                    "Pre-trip inspection / TIV (15 minutes)",
                    reason="Vehicle and trailer inspection before driving in this shift. The 15-minute duration is a planning estimate.",
                )
                self.shift_inspected = True
                continue
            fuel_seconds = math.floor(
                max(0, FUEL_INTERVAL_MILES - self.fuel_miles) / miles_per_second + 1e-8
            )
            if fuel_seconds == 0:
                self.work(30 * 60, "Fueling (30 minutes)", self.location)
                self.fuel_miles = 0.0
                continue
            if self.driving_since_break >= BREAK_LIMIT:
                self._emit(
                    30 * 60,
                    "off_duty",
                    "Driving break (30 minutes)",
                    reason="8 accumulated driving hours without a qualifying 30-minute interruption. Take 30 minutes without driving before continuing; coffee is optional.",
                )
                continue
            seconds = min(
                remaining,
                DRIVE_LIMIT - self.shift_driving,
                WINDOW_LIMIT - (self.now - self.shift_start),
                BREAK_LIMIT - self.driving_since_break,
                CYCLE_LIMIT - self.cycle,
                fuel_seconds,
            )
            self._emit(
                seconds,
                "driving",
                f"Drive to {leg.destination}",
                miles=seconds * miles_per_second,
                location=f"Route leg {leg_index + 1}",
            )
            remaining -= seconds
            # Routing service will attach the actual stop coordinate afterward.
            self.location = f"Along route toward {leg.destination}"
        self.location = leg.destination
