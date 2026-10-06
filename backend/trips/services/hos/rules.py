"""Shared planning limits and the input shape for a route leg.

All durations are integer seconds. Inspection time is a planning estimate.
"""

from dataclasses import dataclass

HOUR = 3600
DRIVE_LIMIT = 11 * HOUR
WINDOW_LIMIT = 14 * HOUR
BREAK_LIMIT = 8 * HOUR
CYCLE_LIMIT = 70 * HOUR
FUEL_INTERVAL_MILES = 1000
INSPECTION_SECONDS = 15 * 60  # Planning estimate, not a prescribed legal duration.


@dataclass(frozen=True)
class Leg:
    distance_miles: float
    duration_seconds: int
    destination: str
