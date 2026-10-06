"""Public scheduling interface; implementation lives in the modules below.

Re-export these names so callers can continue using trips.services.hos.
"""

from .planner import Planner
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
from .schedule import build_schedule, completion_clocks, plan_schedule

__all__ = [
    "Planner",
    "Leg",
    "build_schedule",
    "plan_schedule",
    "completion_clocks",
    "HOUR",
    "DRIVE_LIMIT",
    "WINDOW_LIMIT",
    "BREAK_LIMIT",
    "CYCLE_LIMIT",
    "FUEL_INTERVAL_MILES",
    "INSPECTION_SECONDS",
]
