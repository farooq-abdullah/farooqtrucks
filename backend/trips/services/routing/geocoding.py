"""Resolve location text and name stop coordinates, with 24-hour caching."""

import hashlib
import math
import re

from django.core.cache import cache

from .client import LocationError, RoutingError, _geocoding_request, _suggestions_request
from .photon import photon_results
from .place_names import US_STATES, common_places, expand_query
from .place_reference import regional_reference


def _supported(country, coordinates):
    lon, lat = coordinates
    return (
        isinstance(country, str)
        and country.lower() == "us"
        and -125 <= lon <= -66
        and 24 <= lat <= 50
    )


def suggest_locations(query):
    """Search globally so foreign places remain visible instead of becoming US namesakes."""
    expanded = expand_query(query)
    digest = hashlib.sha256(expanded.casefold().encode("utf-8")).hexdigest()
    key = f"suggestions:v2:{digest}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    places = common_places(expanded)
    if not places:
        data = _suggestions_request({"q": expanded, "limit": 6, "lang": "en"})
        places = photon_results(data)
    suggestions = []
    seen = set()
    for place in places:
        label = place["display_name"]
        if label in seen:
            continue
        seen.add(label)
        suggestions.append(
            {
                "label": label,
                "primary": place["primary"],
                "secondary": place["secondary"],
                "supported": _supported(
                    place["address"]["country_code"], [place["lon"], place["lat"]]
                ),
            }
        )
    # Cache only exact queries; prefix results can omit the correct state/city.
    cache.set(key, suggestions, 86400 if suggestions else 60)
    return suggestions


def geocode(query):
    expanded = expand_query(query)
    digest = hashlib.sha256(expanded.casefold().encode("utf-8")).hexdigest()
    key = f"geocode:v4:{digest}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    # A selected indexed label or an explicit alias resolves to the exact same
    # verified centroid on every serverless instance, without a fuzzy rematch.
    results = common_places(expanded, exact=True)
    if not results and "," not in expanded:
        matching_cities = [
            place
            for place in common_places(expanded)
            if place["primary"].casefold() == expanded.casefold()
        ]
        if len(matching_cities) > 1:
            raise LocationError(
                f'"{query}" matches several cities. Choose a suggestion with its state.'
            )
        results = matching_cities
    if not results:
        results = _geocoding_request(
            "search",
            {
                "q": expanded,
                "accept-language": "en",
                "format": "jsonv2",
                "limit": 6,
                "addressdetails": 1,
            },
        )
    if not isinstance(results, list):
        raise RoutingError("The geocoder returned an invalid response.")
    if not results:
        raise LocationError(
            f'No location found for "{query}". Choose a suggestion or enter a city and state.'
        )
    if any(
        not isinstance(result, dict)
        or not isinstance(result.get("display_name"), str)
        or not isinstance(result.get("address"), dict)
        or not isinstance(result["address"].get("ISO3166-2-lvl4", "") or "", str)
        for result in results
    ):
        raise RoutingError("The geocoder returned an invalid location.")
    # Photon is deliberately typo-tolerant. Never accept a different state or
    # a city-level fallback when a user supplied a numbered street address.
    requested_states = [
        state
        for state in US_STATES.values()
        if re.search(rf",\s*{re.escape(state)}(?:\s*,|\s*$)", expanded, re.IGNORECASE)
    ]
    if requested_states:
        state = requested_states[-1].casefold()
        matches = [
            r
            for r in results
            if str(r.get("address", {}).get("state", "")).casefold() == state
            or str(r.get("address", {}).get("ISO3166-2-lvl4", "") or "").removeprefix("US-")
            in [code for code, name in US_STATES.items() if name.casefold() == state]
        ]
        # Some compatible providers omit state; preserve their validated country
        # result. Explicit conflicting states, however, must never be accepted.
        if matches:
            results = matches
        elif any(r.get("address", {}).get("state") for r in results):
            raise LocationError(
                f"No matching place in {requested_states[-1]}. Choose a suggestion or check the address."
            )
    house = re.match(r"^(\d+[A-Za-z]?)\s+", expanded)
    if house:
        matches = [
            r
            for r in results
            if str(r.get("address", {}).get("house_number", "")).casefold() == house[1].casefold()
            or re.match(rf"^{re.escape(house[1])}\s+", r.get("display_name", ""), re.IGNORECASE)
        ]
        if not matches:
            raise LocationError(
                "That street number could not be verified. Choose a matching address suggestion."
            )
        results = matches
    try:
        result = {
            "query": query,
            "label": results[0]["display_name"],
            "coordinates": [float(results[0]["lon"]), float(results[0]["lat"])],
        }
        if not all(math.isfinite(n) for n in result["coordinates"]):
            raise ValueError("Non-finite coordinates")
        address = results[0].get("address", {})
        country = address["country_code"]
        town = next(
            (
                address[k]
                for k in ("city", "town", "village", "hamlet", "municipality")
                if address.get(k)
            ),
            None,
        )
        state = (address.get("ISO3166-2-lvl4", "") or "").removeprefix("US-") or address.get(
            "state"
        )
        state = next((code for code, name in US_STATES.items() if name == state), state)
        result["log_location"] = f"{town}, {state}" if town and state else result["label"]
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise RoutingError("The geocoder returned an invalid location.") from exc
    if not _supported(country, result["coordinates"]):
        raise LocationError(
            f'"{query}" resolves to {result["label"]}. Choose a location in the contiguous United States.'
        )
    cache.set(key, result, 86400)
    return result


def reverse_label(coordinates):
    """Name every stop without depending on a slow or unavailable public reverse API."""
    return regional_reference(coordinates)
