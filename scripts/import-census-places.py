"""Build the offline place-reference index from the official 2026 Gazetteer."""

import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import requests

SOURCE = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2026_Gazetteer/2026_Gaz_place_national.zip"
response = requests.get(SOURCE, timeout=(5, 30))
response.raise_for_status()
archive = zipfile.ZipFile(io.BytesIO(response.content))
member = next(name for name in archive.namelist() if name.endswith("place_national.txt"))
reader = csv.DictReader(io.StringIO(archive.read(member).decode("utf-8-sig")), delimiter="|")
places = []
for raw in reader:
    row = {key.strip(): value.strip() for key, value in raw.items()}
    if row["USPS"] in {"AK", "HI", "PR"}:
        continue
    lat, lon = float(row["INTPTLAT"]), float(row["INTPTLONG"])
    if not (24 <= lat <= 50 and -125 <= lon <= -66):
        continue
    name = re.sub(r" (?:city|town|village|borough|CDP|municipality)$", "", row["NAME"])
    places.append([name, row["USPS"], row["GEOID"], lat, lon])
assert len(places) > 25000, "Unexpectedly incomplete national places file."
data = {
    "source": SOURCE,
    "source_sha256": hashlib.sha256(response.content).hexdigest(),
    "year": 2026,
    "columns": ["name", "state", "geoid", "latitude", "longitude"],
    "places": places,
}
destination = Path(__file__).resolve().parent.parent / "backend/trips/services/routing/us_places_2026.json.gz"
destination.write_bytes(gzip.compress(json.dumps(data, separators=(",", ":")).encode("utf-8"), mtime=0))
print(f"Saved {len(places):,} verified places ({destination.stat().st_size:,} bytes).")
print(f"Source SHA-256: {data['source_sha256']}")
