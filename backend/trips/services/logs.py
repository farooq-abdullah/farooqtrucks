"""Split schedule events at midnight and fill every sheet to 24 hours."""

import math
from datetime import datetime, timedelta

STATUSES = ("off_duty", "sleeper_berth", "driving", "on_duty")


def daily_logs(events, position_at=None, road_at=None, place_at=None):
    first = datetime.fromisoformat(events[0]["start"])
    finish = datetime.fromisoformat(events[-1]["end"])
    midnight = first.replace(hour=0, minute=0, second=0, microsecond=0)
    logs = []
    # A completion exactly at midnight belongs to the preceding sheet.
    while midnight < finish:
        day_end = midnight + timedelta(days=1)
        pieces = []
        remarks = []
        for event in events:
            start = datetime.fromisoformat(event["start"])
            end = datetime.fromisoformat(event["end"])
            clipped_start, clipped_end = max(start, midnight), min(end, day_end)
            if clipped_end <= clipped_start:
                continue
            seconds = (clipped_end - clipped_start).total_seconds()
            activity = event["activity"]
            coordinates, location = event.get("coordinates"), event["location"]
            road = event.get("road")
            route_reference = event.get("route_reference")
            if start < midnight:
                activity = f"Continue {activity[:1].lower() + activity[1:]}"
                if event["status"] == "driving":
                    # A moving truck is not at its previous stop at midnight.
                    if position_at or road_at:
                        fraction = (midnight - start).total_seconds() / event["duration_seconds"]
                        midnight_miles = (
                            event["start_route_miles"] + fraction * event["distance_miles"]
                        )
                    # The event's starting road can be hundreds of miles away.
                    # Resolve the new road, or leave it unknown rather than stale.
                    road = road_at(midnight_miles) if road_at else None
                    if position_at:
                        coordinates = position_at(midnight_miles)
                        route_reference = (
                            f"{road} · " if road else ""
                        ) + f"{midnight_miles:,.0f} mi into trip"
                        location = (
                            f"In transit · {place_at(midnight_miles)}"
                            if place_at
                            else f"In transit · {route_reference}"
                        )
                    else:
                        coordinates, location = None, "In transit; position not supplied"
            pieces.append(
                {
                    "status": event["status"],
                    "start_minute": (clipped_start - midnight).total_seconds() / 60,
                    "end_minute": (clipped_end - midnight).total_seconds() / 60,
                    "distance_miles": event["distance_miles"] * seconds / event["duration_seconds"],
                    "activity": activity,
                    "location": location,
                    "coordinates": coordinates,
                    "road": road,
                    "route_reference": route_reference,
                    "reason": event.get("reason"),
                    "event_start": event["start"],
                    "event_end": event["end"],
                }
            )
            remarks.append(
                {
                    "time": clipped_start.strftime("%H:%M:%S"),
                    "activity": activity,
                    "location": location,
                    "road": road,
                    "route_reference": route_reference,
                    "reason": event.get("reason"),
                    "coordinates": coordinates,
                }
            )
        if pieces[0]["start_minute"] > 0:
            pieces.insert(
                0,
                {
                    "status": "off_duty",
                    "start_minute": 0,
                    "end_minute": pieces[0]["start_minute"],
                    "distance_miles": 0,
                    "activity": "Off duty before planned departure",
                    "location": events[0]["location"],
                    "reason": "Assumed off-duty time before the trip; not an actual activity record.",
                },
            )
            remarks.insert(
                0,
                {
                    "time": "00:00:00",
                    "activity": "Off duty before planned departure",
                    "location": events[0]["location"],
                    "coordinates": events[0].get("coordinates"),
                },
            )
        if pieces[-1]["end_minute"] < 1440:
            pieces.append(
                {
                    "status": "off_duty",
                    "start_minute": pieces[-1]["end_minute"],
                    "end_minute": 1440,
                    "distance_miles": 0,
                    "activity": "Trip complete; off duty",
                    "location": events[-1]["location"],
                    "reason": "Assumed off-duty time after completion; update your official log with actual activity.",
                }
            )
            remarks.append(
                {
                    "time": finish.strftime("%H:%M:%S"),
                    "activity": "Trip complete; off duty",
                    "location": events[-1]["location"],
                    "coordinates": events[-1].get("end_coordinates"),
                }
            )
        # Horizontal lines continue when adjacent events share the same status.
        segments = []
        for piece in pieces:
            if segments and segments[-1]["status"] == piece["status"]:
                segments[-1]["end_minute"] = piece["end_minute"]
                segments[-1]["distance_miles"] += piece["distance_miles"]
            else:
                segments.append(
                    {
                        key: piece[key]
                        for key in ("status", "start_minute", "end_minute", "distance_miles")
                    }
                )
        totals = {
            status: sum(
                (p["end_minute"] - p["start_minute"]) / 60 for p in pieces if p["status"] == status
            )
            for status in STATUSES
        }
        # Allocate rounding remainders so printed H:M totals also sum to 24:00.
        displayed_minutes = {
            status: math.floor(hours * 60 + 1e-8) for status, hours in totals.items()
        }
        order = sorted(
            STATUSES,
            key=lambda status: totals[status] * 60 - displayed_minutes[status],
            reverse=True,
        )
        for status in order[: 1440 - sum(displayed_minutes.values())]:
            displayed_minutes[status] += 1
        logs.append(
            {
                "date": midnight.date().isoformat(),
                "clock": midnight.strftime("UTC%z"),
                "segments": segments,
                "activities": pieces,
                "totals_hours": totals,
                "totals_minutes": displayed_minutes,
                "total_hours": sum(totals.values()),
                "distance_miles": sum(p["distance_miles"] for p in pieces),
                "remarks": remarks,
            }
        )
        midnight = day_end
    return logs
