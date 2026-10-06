"""Validate Photon features and adapt them to the planner's location contract."""

import math

from .client import RoutingError


def photon_results(data):
    if not isinstance(data, dict) or not isinstance(data.get("features"), list):
        raise RoutingError("The location service returned an invalid response.")
    results = []
    for feature in data["features"]:
        try:
            props = feature["properties"]
            coordinates = [float(n) for n in feature["geometry"]["coordinates"]]
            if (
                len(coordinates) != 2
                or not all(math.isfinite(n) for n in coordinates)
                or not -180 <= coordinates[0] <= 180
                or not -90 <= coordinates[1] <= 90
            ):
                continue
            street = " ".join(str(props[k]) for k in ("housenumber", "street") if props.get(k))
            parts = []
            for key, part in (
                ("name", props.get("name")),
                ("street", street),
                ("city", props.get("city")),
                ("district", props.get("district")),
                ("state", props.get("state")),
                ("postcode", props.get("postcode")),
                ("country", props.get("country")),
            ):
                if part and (
                    key == "state" or str(part).casefold() not in {p.casefold() for p in parts}
                ):
                    parts.append(str(part))
            label = ", ".join(parts)
            if not label or len(label) > 200:
                continue
            town = props.get("city") or (
                props.get("name")
                if props.get("osm_value") in ("city", "town", "village", "hamlet")
                or props.get("type") in ("city", "locality")
                else None
            )
            results.append(
                {
                    "display_name": label,
                    "lon": coordinates[0],
                    "lat": coordinates[1],
                    "primary": parts[0],
                    "secondary": ", ".join(parts[1:]),
                    "address": {
                        "country_code": str(props.get("countrycode", "")).lower(),
                        "state": props.get("state"),
                        "city": town,
                        "county": props.get("county"),
                        "house_number": props.get("housenumber"),
                        "road": props.get("street"),
                    },
                }
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    if data["features"] and not results:
        raise RoutingError("The location service returned invalid places.")
    return results
