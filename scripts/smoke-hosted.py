"""Verify public HTML, assets, API and trip invariants without account cookies."""

import json
import math
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

origin = sys.argv[1].rstrip('/')
assert urlparse(origin).scheme == 'https', 'Use the HTTPS production origin.'
session = requests.Session()
session.headers['User-Agent'] = 'farooqtrucks-release-check/1.0'
report = {'origin': origin, 'checks': []}


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    report['checks'].append(label)
    print('PASS:', label, flush=True)


html = session.get(origin + '/plan', timeout=40)
print('Public HTML response:', html.status_code, html.url, html.text[:250], flush=True)
check(html.status_code == 200 and 'farooqtrucks' in html.text, 'Public React page without authentication')
for path in ('/route', '/logs'):
    response = session.get(origin + path, timeout=30)
    check(response.status_code == 200 and response.text == html.text, f'Direct {path} navigation')
for path in re.findall(r'(?:src|href)="(/assets/[^"]+)"', html.text):
    response = session.get(origin + path, timeout=30)
    check(response.status_code == 200 and bool(response.content), f'Built asset {path}')
health = session.get(origin + '/api/health/', timeout=30)
check(health.status_code == 200 and health.json()['status'] == 'ok', 'Public Django API health')

for abbreviation, city in (('NY', 'New York'), ('LA', 'Los Angeles'), ('SF', 'San Francisco')):
    started = time.monotonic()
    response = session.get(origin + '/api/locations/search/', params={'q': abbreviation}, timeout=30)
    elapsed = time.monotonic() - started
    check(response.status_code == 200, f'{abbreviation} location search')
    suggestions = response.json()['suggestions']
    check(any(city in p['label'] and p['supported'] for p in suggestions), f'{abbreviation} resolves to {city}')
    report.setdefault('search_seconds', {})[abbreviation] = round(elapsed, 3)

cases = [
    ('short', 'Chicago, IL', 'Springfield, IL', 'St. Louis, MO', 20),
    ('cycle-exhausted', 'Chicago, IL', 'Springfield, IL', 'St. Louis, MO', 70),
    ('long', 'LA', 'Dallas, TX', 'NY', 68),
    ('same-location', 'Chicago, IL', 'Chicago, IL', 'Chicago, IL', 0),
]
for name, current, pickup, dropoff, cycle in cases:
    started = time.monotonic()
    response = session.post(origin + '/api/trips/plan/', json={
        'current_location': current, 'pickup_location': pickup,
        'dropoff_location': dropoff, 'current_cycle_used': cycle,
    }, timeout=120)
    check(response.status_code == 200, f'{name} route calculation (HTTP {response.status_code})')
    plan = response.json()
    events, logs = plan['events'], plan['daily_logs']
    check(len(logs) == plan['summary']['log_days'], f'{name} daily sheet count')
    check(all(sum(day['totals_minutes'].values()) == 1440 for day in logs), f'{name} complete 24-hour sheets')
    check(all(math.isfinite(n) for n in (plan['summary']['distance_miles'], plan['summary']['driving_hours'])), f'{name} finite route totals')
    check(abs(sum(e['duration_seconds'] for e in events if e['status'] == 'driving') / 3600 - plan['summary']['driving_hours']) < 1e-8, f'{name} driving time conservation')
    check(all(datetime.fromisoformat(a['end']) == datetime.fromisoformat(b['start']) for a, b in zip(events, events[1:])), f'{name} contiguous event timeline')
    check(all('Along route at' not in item['location'] and 'In transit at' not in item['location'] for item in events + [remark for day in logs for remark in day['remarks']]), f'{name} readable location references instead of bare coordinates')
    check(sum(e['duration_seconds'] for e in events if e['activity'].startswith('Pickup')) == 3600, f'{name} one-hour pickup')
    check(sum(e['duration_seconds'] for e in events if e['activity'].startswith('Drop-off')) == 3600, f'{name} one-hour drop-off')
    if name in ('cycle-exhausted', 'long'):
        check(plan['summary']['cycle_restarts'] >= 1 and len(logs) > 1, f'{name} cycle restart and multiple days')
    if name == 'long':
        check(plan['summary']['fuel_stops'] >= 1, 'Long route scheduled fueling')
        estimated = [event for event in events if event.get('location_estimated')]
        check(bool(estimated) and all(event['location'].startswith(('Near ', 'About ')) for event in estimated), 'Bundled named places work on the hosted long trip')
    output = Path('artifacts/hosted')
    output.mkdir(parents=True, exist_ok=True)
    (output / f'{name}.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    report.setdefault('trip_seconds', {})[name] = round(time.monotonic() - started, 3)

bad = session.post(origin + '/api/trips/plan/', json={'current_cycle_used': 71}, timeout=30)
check(bad.status_code == 400, 'Invalid trip is rejected with HTTP 400')
output = Path('artifacts/hosted')
output.mkdir(parents=True, exist_ok=True)
(output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('All public deployment checks passed.', flush=True)
