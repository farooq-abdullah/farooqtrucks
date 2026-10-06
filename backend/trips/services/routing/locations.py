"""Find planned positions along the road and attach location remarks.

RouteLocator indexes the polyline; annotate_schedule enriches scheduled events
using those positions and the already resolved trip locations.
"""

import math
from bisect import bisect_left
from dataclasses import dataclass

from .client import RoutingError
from .geocoding import reverse_label


def _haversine(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371000 * 2 * math.asin(min(1, math.sqrt(h)))


@dataclass
class RouteLocator:
    """Locate a planned mileage on the route polyline, never on a straight chord."""

    legs: list

    def __post_init__(self):
        self.indexes = []
        for leg in self.legs:
            points = leg["geometry"]["coordinates"]
            cumulative = [0.0]
            for a, b in zip(points, points[1:]):
                cumulative.append(cumulative[-1] + _haversine(a, b))
            self.indexes.append((points, cumulative))

    def at(self, miles):
        remaining = max(0.0, miles)
        for index, leg in enumerate(self.legs):
            if remaining <= leg["distance_miles"] + 1e-8 or index == len(self.legs) - 1:
                points, cumulative = self.indexes[index]
                fraction = min(1, remaining / leg["distance_miles"]) if leg["distance_miles"] else 0
                target = fraction * cumulative[-1]
                right = min(len(points) - 1, max(1, bisect_left(cumulative, target)))
                left = right - 1
                span = cumulative[right] - cumulative[left]
                ratio = (target - cumulative[left]) / span if span else 0
                return [
                    points[left][axis] + ratio * (points[right][axis] - points[left][axis])
                    for axis in (0, 1)
                ]
            remaining -= leg["distance_miles"]
        return self.indexes[-1][0][-1]

    def road_at(self, miles):
        """OSRM road at the estimated mileage; no invented milepost/facility."""
        remaining = max(0.0, miles)
        for index, leg in enumerate(self.legs):
            if remaining <= leg["distance_miles"] + 1e-8 or index == len(self.legs) - 1:
                steps = leg.get("instructions", [])
                for step in steps:
                    if remaining < step["distance_miles"]:
                        return step.get("road") or None
                    remaining -= step["distance_miles"]
                return steps[-1].get("road") if steps else None
            remaining -= leg["distance_miles"]
        return None


def annotate_schedule(events, route, locations):
    locator = RouteLocator(route["legs"])
    warnings = []
    resolved = {}
    boundaries = [(0.0, locations[0])]
    mileage = 0.0
    for leg, location in zip(route["legs"], locations[1:]):
        mileage += leg["distance_miles"]
        boundaries.append((mileage, location))
    for event in events:
        coordinates = locator.at(event["start_route_miles"])
        event["coordinates"] = coordinates
        event["end_coordinates"] = locator.at(event["end_route_miles"])
        event["road"] = locator.road_at(event["start_route_miles"])
        if event["location"].startswith(("Along route", "Route leg")):
            known = next(
                (
                    location
                    for miles, location in boundaries
                    if math.isclose(event["start_route_miles"], miles, abs_tol=1e-6, rel_tol=0)
                ),
                None,
            )
            if known is not None:
                # These are actual leg endpoints already resolved from the input.
                # Keep the road-snapped geometry and use its known city/state;
                # reserve reverse lookup for estimated intermediate positions.
                event["location"] = known.get("log_location", known["label"])
                continue
            key = tuple(round(n, 4) for n in coordinates)
            if key not in resolved:
                try:
                    resolved[key] = reverse_label(coordinates)
                except RoutingError:
                    resolved[key] = f"Along route at {coordinates[1]:.4f}, {coordinates[0]:.4f}"
                    warnings.append(
                        "Some stop locations could not be named; their coordinates are included."
                    )
            event["location"] = resolved[key]
        else:
            # Exact pickup/current/dropoff labels are already geocoded.
            for location in locations:
                if event["location"] == location["label"]:
                    event["location"] = location.get("log_location", location["label"])
                    event["coordinates"] = location["coordinates"]
                    if event["status"] != "driving":
                        event["end_coordinates"] = location["coordinates"]
                    break
    return list(dict.fromkeys(warnings))
