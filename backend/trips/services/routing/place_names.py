"""Common city shorthand; expansion uses real geocoder results, never invented pins."""

import json
import re
from functools import lru_cache
from pathlib import Path

CITY_ALIASES = {
    "ny": "New York, New York, United States",
    "nyc": "New York, New York, United States",
    "new york city": "New York, New York, United States",
    "la": "Los Angeles, California, United States",
    "l.a.": "Los Angeles, California, United States",
    "sf": "San Francisco, California, United States",
    "sfo": "San Francisco, California, United States",
    "san fran": "San Francisco, California, United States",
    "dc": "Washington, District of Columbia, United States",
    "d.c.": "Washington, District of Columbia, United States",
    "washington dc": "Washington, District of Columbia, United States",
    "vegas": "Las Vegas, Nevada, United States",
    "lv": "Las Vegas, Nevada, United States",
    "chi": "Chicago, Illinois, United States",
    "atl": "Atlanta, Georgia, United States",
    "philly": "Philadelphia, Pennsylvania, United States",
    "phx": "Phoenix, Arizona, United States",
    "stl": "Saint Louis, Missouri, United States",
    "st. louis, mo": "Saint Louis, Missouri, United States",
    "st louis, mo": "Saint Louis, Missouri, United States",
    "nola": "New Orleans, Louisiana, United States",
}

US_STATES = dict(
    zip(
        "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split(),
        "Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|District of Columbia".split(
            "|"
        ),
        strict=True,
    )
)


def expand_query(query):
    text = " ".join(query.strip().split())
    alias = CITY_ALIASES.get(text.casefold())
    if alias:
        return alias
    # A trailing state abbreviation is context, not a standalone city alias.
    # In particular "Baton Rouge, LA" must remain in Louisiana.
    match = re.search(r"(?:,\s*|\s+)([A-Za-z]{2})(?:\s+(\d{5}(?:-\d{4})?))?$", text)
    if match and match[1].upper() in US_STATES:
        postcode = f", {match[2]}" if match[2] else ""
        return f"{text[: match.start()]}, {US_STATES[match[1].upper()]}{postcode}, United States"
    return text


@lru_cache(maxsize=1)
def _common_places():
    from .photon import photon_results

    return photon_results(
        json.loads(Path(__file__).with_name("common_places.json").read_text(encoding="utf-8"))
    )


def common_places(query, *, exact=False):
    """Return verified city centroids only, with explicit state/country labels.

    This deliberately small index does not guess addresses or reinterpret a
    foreign place as a similarly named US town. Other queries go to Photon.
    """
    normalized = re.sub(r"[^a-z0-9]+", " ", query.casefold()).strip()
    if len(normalized) < 2:
        return []
    results = []
    for place in _common_places():
        label = re.sub(r"[^a-z0-9]+", " ", place["display_name"].casefold()).strip()
        if label == normalized or (not exact and label.startswith(normalized)):
            results.append(place)
    return results[:6]
