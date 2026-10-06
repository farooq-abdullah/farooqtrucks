"""Resolve the planned terminal clock and create its default departure time."""

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from timezonefinder import timezone_at


def terminal_clock():
    offset = settings.LOG_UTC_OFFSET
    if not re.fullmatch(r"[+-](?:0\d|1[0-4]):[0-5]\d", offset):
        raise ValueError("LOG_UTC_OFFSET must be a fixed UTC offset such as -06:00.")
    hours, minutes = map(int, offset[1:].split(":"))
    delta = timedelta(hours=hours, minutes=minutes)
    return timezone(delta if offset[0] == "+" else -delta)


def timezone_for_location(coordinates):
    """Find the IANA timezone for geocoded [longitude, latitude] coordinates."""
    longitude, latitude = coordinates
    zone_name = timezone_at(lng=longitude, lat=latitude)
    if zone_name is None:
        return terminal_clock(), None
    return ZoneInfo(zone_name), zone_name


def default_departure(clock):
    """Use 08:00 on today's date in the selected terminal timezone."""
    return datetime.now(clock).replace(
        hour=settings.DEFAULT_DEPARTURE_HOUR, minute=0, second=0, microsecond=0
    )


def fixed_offset_clock(moment):
    """Keep 24-hour planned log sheets on the offset in effect at trip start."""
    return timezone(moment.utcoffset())
