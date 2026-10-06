"""Thin HTTP layer: validate, call services, return JSON."""

from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .clock import default_departure, fixed_offset_clock, timezone_for_location
from .serializers import TripRequestSerializer
from .services.hos import Leg, build_schedule, completion_clocks
from .services.logs import daily_logs
from .services.routing import (
    LocationError,
    RouteLocator,
    RoutingError,
    annotate_schedule,
    geocode,
    road_route,
    suggest_locations,
)


class LocationSearchThrottle(AnonRateThrottle):
    scope = "location_search"


@api_view(["GET"])
@throttle_classes([LocationSearchThrottle])
def location_search(request):
    query = request.query_params.get("q", "").strip()
    if not 2 <= len(query) <= 200:
        return Response(
            {"detail": "Enter between 2 and 200 characters to search for a place."}, status=400
        )
    try:
        return Response({"suggestions": suggest_locations(query)})
    except RoutingError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["GET"])
@throttle_classes([])
def health(request):
    return Response(
        {
            "status": "ok",
            "database_required": False,
        }
    )


@api_view(["POST"])
def plan_trip(request):
    serializer = TripRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    try:
        locations = []
        for key in ("current_location", "pickup_location", "dropoff_location"):
            try:
                locations.append(geocode(values[key]))
            except LocationError as exc:
                return Response({key: [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        location_clock, timezone_name = timezone_for_location(locations[0]["coordinates"])
        departure = default_departure(location_clock)
        departure = departure.astimezone(fixed_offset_clock(departure))
        route = road_route(locations)
        legs = [
            Leg(leg["distance_miles"], leg["duration_seconds"], locations[i + 1]["label"])
            for i, leg in enumerate(route["legs"])
        ]
        schedule = build_schedule(
            legs, departure, values["current_cycle_used"], locations[0]["label"]
        )
        events = schedule.events
        warnings = annotate_schedule(events, route, locations)
    except RoutingError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    locator = RouteLocator(route["legs"])
    logs = daily_logs(events, position_at=locator.at, road_at=locator.road_at)
    total_seconds = sum(event["duration_seconds"] for event in events)
    timezone_label = timezone_name or f"Configured fallback {departure.strftime('%z')}"
    if timezone_name is None:
        warnings.append(
            "Could not identify a time zone for the starting coordinates; the configured "
            "LOG_UTC_OFFSET fallback was used."
        )
    return Response(
        {
            "locations": locations,
            "route": route,
            "events": events,
            "daily_logs": logs,
            "summary": {
                "distance_miles": route["distance_miles"],
                "driving_hours": route["driving_seconds"] / 3600,
                "elapsed_hours": total_seconds / 3600,
                "departure_time": events[0]["start"],
                "arrival_time": schedule.dropoff_arrival.isoformat(),
                "completion_time": events[-1]["end"],
                "log_days": len(logs),
                "fuel_stops": sum(e["activity"].startswith("Fueling") for e in events),
                "cycle_restarts": sum(e["activity"].startswith("Cycle restart") for e in events),
                "inspections": sum("inspection / TIV" in e["activity"] for e in events),
            },
            "clocks": completion_clocks(schedule),
            "planning_parameters": {
                "initial_cycle_hours": values["current_cycle_used"],
                "cycle_limit_hours": 70,
                "cycle_days": 8,
                "prior_rest_hours": 10,
                "pickup_hours": 1,
                "dropoff_hours": 1,
                "inspection_minutes": 15,
                "time_zone": timezone_label,
                "time_zone_offset": departure.strftime("%z"),
            },
            "warnings": warnings,
        }
    )
