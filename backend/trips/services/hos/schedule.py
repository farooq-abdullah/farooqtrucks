"""Build a complete two-leg trip and report the final driver clocks."""

from datetime import timedelta

from .planner import Planner
from .rules import BREAK_LIMIT, CYCLE_LIMIT, DRIVE_LIMIT, HOUR, WINDOW_LIMIT


def build_schedule(legs, departure, cycle_used, current_location):
    if len(legs) != 2:
        raise ValueError("A trip must have current-to-pickup and pickup-to-dropoff legs.")
    planner = Planner(departure, cycle_used, current_location)
    planner.drive(legs[0], 0)
    planner.work(HOUR, "Pickup (1 hour)", legs[0].destination)
    planner.drive(legs[1], 1)
    planner.dropoff_arrival = departure + timedelta(seconds=planner.now)
    planner.work(HOUR, "Drop-off (1 hour)", legs[1].destination)
    planner.finish_shift()
    return planner


def plan_schedule(legs, departure, cycle_used, current_location):
    return build_schedule(legs, departure, cycle_used, current_location).events


def completion_clocks(planner):
    """Expose scheduler state so the UI never guesses remaining driver hours."""
    elapsed = planner.now - planner.shift_start
    return {
        "driving_used_hours": planner.shift_driving / HOUR,
        "driving_remaining_hours": max(0, DRIVE_LIMIT - planner.shift_driving) / HOUR,
        "shift_used_hours": elapsed / HOUR,
        "shift_remaining_hours": max(0, WINDOW_LIMIT - elapsed) / HOUR,
        "break_driving_hours": planner.driving_since_break / HOUR,
        "break_remaining_hours": max(0, BREAK_LIMIT - planner.driving_since_break) / HOUR,
        "cycle_used_hours": planner.cycle / HOUR,
        "cycle_remaining_hours": max(0, CYCLE_LIMIT - planner.cycle) / HOUR,
    }
