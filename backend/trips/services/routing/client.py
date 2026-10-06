"""Bounded map requests with per-thread connection reuse.

Photon supports search-as-you-type and serverless deployment. A slow upstream
request must never hold a process-wide lock that queues later keystrokes.
"""

import threading
import time

import requests
from django.conf import settings

_geocode_lock = threading.Lock()
_last_geocode = 0.0
_http = threading.local()


class RoutingError(Exception):
    """A public map provider could not return a usable result."""


class LocationError(RoutingError):
    """The entered place could not be used for a supported trip."""


def _request(url, params, *, timeout=(3, 12)):
    try:
        if not hasattr(_http, "session"):
            _http.session = requests.Session()
        response = _http.session.get(
            url,
            params=params,
            headers={"User-Agent": settings.MAP_USER_AGENT, "Accept": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RoutingError("The map service is unavailable. Please try again shortly.") from exc


def _geocoding_request(endpoint, params):
    if settings.GEOCODING_PROVIDER == "photon":
        # Preserve a common location shape for the planner, independent of the
        # provider. Reverse lookup is optional enrichment, so fail quickly.
        from .photon import photon_results

        search = endpoint == "search"
        photon_params = (
            {"q": params["q"], "limit": params.get("limit", 6), "lang": "en"}
            if search
            else {"lon": params["lon"], "lat": params["lat"], "limit": 1, "lang": "en"}
        )
        data = _request(
            f"{settings.GEOCODING_BASE_URL.rstrip('/')}/{'api' if search else 'reverse'}/",
            photon_params,
            timeout=(2, 6) if search else (1, 2),
        )
        results = photon_results(data)
        return results if search else (results[0] if results else {"address": {}})

    # Explicit opt-in for an existing Nominatim-compatible deployment. A public
    # instance requires one worker; production should use a private provider.
    global _last_geocode
    with _geocode_lock:
        wait = 1.05 - (time.monotonic() - _last_geocode)
        if wait > 0:
            time.sleep(wait)
        try:
            return _request(f"{settings.GEOCODING_BASE_URL.rstrip('/')}/{endpoint}", params)
        finally:
            _last_geocode = time.monotonic()


def _suggestions_request(params):
    """Debounced, cached and API-throttled searches; never queue behind old I/O."""
    return _request(f"{settings.LOCATION_SEARCH_BASE_URL.rstrip('/')}/api/", params, timeout=(2, 6))
