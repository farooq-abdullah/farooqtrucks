# Geographic references for estimated stops

`us_places_2026.json.gz` contains 31,553 contiguous-US places from the official
2026 US Census National Places Gazetteer. The importer preserves GEOID, USPS
state, and the published internal-point coordinates. Common legal-type suffixes
such as “city”, “village” and “CDP” are removed from display names.

Source: https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
Archive: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2026_Gazetteer/2026_Gaz_place_national.zip
Retrieved: October 6, 2026.
Archive SHA-256: af678e2d990827c89ee39b98c82de6e90b693c7361ff0e559ae3076670dd2863

Rebuild from the repository root: `python scripts/import-census-places.py`.

The nearest reference is selected by spherical distance. “About X mi NE of …”
describes an approximate straight-line distance and bearing from the published
reference point. It does not assert that the stop lies inside a city's boundary,
identify a highway milepost, or name a parking/fuel facility. Actual planned
coordinates remain on the route; naming does not move stops or change clocks.

US Census government data is public-domain material. These place references
require no live reverse-geocoding request or API key. When unavailable, the app
shows the route's road reference and distance into the trip.
