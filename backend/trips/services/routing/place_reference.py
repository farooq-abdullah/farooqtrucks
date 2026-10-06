"""Describe estimated route positions relative to verified Census places.

These are geographic references, not fuel businesses or parking facilities.
Distances are approximate great-circle distances from a Gazetteer internal point.
"""

import gzip
import json
import math
from functools import lru_cache
from pathlib import Path

from .client import RoutingError


def _vector(lon, lat):
    lon, lat = math.radians(lon), math.radians(lat)
    return math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)


@lru_cache(maxsize=1)
def _places():
    try:
        with gzip.open(Path(__file__).with_name("us_places_2026.json.gz"), "rt") as source:
            data = json.load(source)
        places = tuple((row, _vector(row[4], row[3])) for row in data["places"])
        if not places:
            raise ValueError("The place-reference index is empty.")
        return places
    except (OSError, EOFError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise RoutingError(
            "Place references are unavailable; use the road and trip mileage."
        ) from exc


@lru_cache(maxsize=2048)
def _reference(lon, lat):
    vector = _vector(lon, lat)
    place, point = max(_places(), key=lambda item: sum(a * b for a, b in zip(item[1], vector)))
    name, state, _, place_lat, place_lon = place
    distance = 3958.7613 * math.acos(min(1, max(-1, sum(a * b for a, b in zip(point, vector)))))
    if distance < 0.5:
        return f"Near {name}, {state}"
    latitude, origin_latitude = math.radians(lat), math.radians(place_lat)
    longitude = math.radians(lon - place_lon)
    bearing = (
        math.degrees(
            math.atan2(
                math.sin(longitude) * math.cos(latitude),
                math.cos(origin_latitude) * math.sin(latitude)
                - math.sin(origin_latitude) * math.cos(latitude) * math.cos(longitude),
            )
        )
        % 360
    )
    direction = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")[int((bearing + 22.5) // 45) % 8]
    return f"About {max(1, round(distance))} mi {direction} of {name}, {state}"


def regional_reference(coordinates):
    lon, lat = coordinates
    if not (math.isfinite(lon) and math.isfinite(lat) and -125 <= lon <= -66 and 24 <= lat <= 50):
        raise RoutingError("No supported place reference for this route position.")
    return _reference(lon, lat)
