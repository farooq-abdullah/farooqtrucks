"""Convert an OSRM road route into our route/leg/instruction JSON format.

OSRM's general road profile does not model truck restrictions or live traffic.
"""

import math

from django.conf import settings

from .client import RoutingError, _request

METERS_PER_MILE = 1609.344
MAX_ROUTE_MILES = 10000
MAX_DRIVING_SECONDS = 30 * 24 * 3600
MAX_PROVIDER_SPEED_MPH = 200  # Defensive sanity bound, not a legal driving speed.


def _number(value):
    """Validate provider JSON numbers before arithmetic or integer conversion."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a number")
    if not math.isfinite(value) or value < 0:
        raise ValueError("Expected a finite nonnegative number")
    return value


def _point(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("Expected a longitude/latitude pair")
    for axis, limit in zip(value, (180, 90)):
        if (
            isinstance(axis, bool)
            or not isinstance(axis, (int, float))
            or not math.isfinite(axis)
            or not -limit <= axis <= limit
        ):
            raise ValueError("Invalid route coordinate")
    return value


def _line(geometry):
    if not isinstance(geometry, dict) or geometry.get("type") != "LineString":
        raise ValueError("Expected a GeoJSON LineString")
    points = geometry["coordinates"]
    if not isinstance(points, list) or not points:
        raise ValueError("Empty route geometry")
    return [_point(point) for point in points]


def _text(value):
    if not isinstance(value, str):
        raise ValueError("Expected maneuver text")
    return value


def road_route(locations):
    coordinate_text = ";".join(f"{p['coordinates'][0]},{p['coordinates'][1]}" for p in locations)
    data = _request(
        f"{settings.OSRM_BASE_URL.rstrip('/')}/route/v1/driving/{coordinate_text}",
        {
            "steps": "true",
            "geometries": "geojson",
            "overview": "full",
        },
    )
    try:
        if data["code"] != "Ok" or not data.get("routes"):
            raise RoutingError("No drivable route was found between these locations.")
        source = data["routes"][0]
        source_legs = source["legs"]
        if not isinstance(source_legs, list) or len(source_legs) != 2:
            raise ValueError("Expected two route legs")
        overview = _line(source["geometry"])
        legs = []
        for source_leg in source_legs:
            distance = _number(source_leg["distance"]) / METERS_PER_MILE
            duration = math.ceil(_number(source_leg["duration"]))
            if distance * 3600 > MAX_PROVIDER_SPEED_MPH * max(1, duration):
                raise ValueError("Implausible route speed")
            steps = source_leg["steps"]
            if not isinstance(steps, list) or not steps:
                raise ValueError("Missing route steps")
            coordinates = []
            instructions = []
            for step in steps:
                points = _line(step["geometry"])
                coordinates.extend(
                    points[1:]
                    if coordinates and points and coordinates[-1] == points[0]
                    else points
                )
                maneuver = step["maneuver"]
                kind = _text(maneuver["type"]).replace("_", " ")
                modifier = _text(maneuver.get("modifier", "")).replace("_", " ")
                name = _text(step.get("name", ""))
                reference = _text(step.get("ref", ""))
                name = name or reference or "the road"
                instruction = f"{kind.capitalize()} {modifier} on {name}".replace("  ", " ")
                step_distance = _number(step["distance"]) / METERS_PER_MILE
                step_duration = math.ceil(_number(step["duration"]))
                if step_distance > MAX_ROUTE_MILES or step_duration > MAX_DRIVING_SECONDS:
                    raise ValueError("Implausible route step")
                instructions.append(
                    {
                        "instruction": instruction,
                        "road": " · ".join(
                            dict.fromkeys(filter(None, (reference, step.get("name"))))
                        ),
                        "distance_miles": step_distance,
                        "duration_seconds": step_duration,
                        "coordinates": _point(maneuver["location"]),
                    }
                )
            if distance > 0 and not any(point != coordinates[0] for point in coordinates[1:]):
                raise ValueError("Moving leg has no route geometry")
            # A stationary leg can legitimately contain one coordinate. Duplicate
            # it so the downstream geometry remains a valid two-point LineString.
            if len(coordinates) == 1:
                coordinates.append(coordinates[0][:])
            # Even a provider's rounded zero-second leg must account for movement.
            legs.append(
                {
                    "distance_miles": distance,
                    "duration_seconds": max(1, duration) if distance > 0 else 0,
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                    "instructions": instructions,
                }
            )
        if sum(p["distance_miles"] for p in legs) > MAX_ROUTE_MILES:
            raise RoutingError("Please use a route of at most 10,000 miles with three locations.")
        if sum(p["duration_seconds"] for p in legs) > MAX_DRIVING_SECONDS:
            raise RoutingError(
                "The routing service returned an implausible driving duration. Please try again."
            )
        if sum(p["distance_miles"] for p in legs) > 0 and not any(
            point != overview[0] for point in overview[1:]
        ):
            raise ValueError("Moving route has no overview geometry")
        if len(overview) == 1:
            overview.append(overview[0][:])
        return {
            "provider": "OSRM",
            "profile": "general road route",
            "geometry": {"type": "LineString", "coordinates": overview},
            "legs": legs,
            "distance_miles": sum(p["distance_miles"] for p in legs),
            "driving_seconds": sum(p["duration_seconds"] for p in legs),
        }
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as exc:
        raise RoutingError(
            "The routing service returned an incomplete route. Please try again."
        ) from exc
