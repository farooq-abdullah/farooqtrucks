# farooqtrucks

A Django + React/MUI trip planner with road routing, scheduled stops and rests,
driver clocks, and filled 24-hour daily log sheets. The responsive frontend follows
the approved farooqtrucks Figma design. It supports route instructions, day selection,
optional sheet details, activity tooltips, JSON download
and printing every log day to PDF.

The app suggests a trip plan, then fills log sheets from that plan. It does not
record actual duty changes. Hover, focus or tap a timeline line to see its
activity, time, location and scheduling reason. Driving plus other on-duty work
forms the daily working total; breaks and sleeper time are excluded.

The daily sheets show planned activities. Duty-change times preserve seconds;
displayed status totals are apportioned to whole minutes and sum to 24:00.
The driver signature field has been removed from the UI, print and JSON export.

The assessment checklist, deployment instructions and Loom walkthrough outline are
in [docs/SUBMISSION.md](docs/SUBMISSION.md).
The complete guide/video review and source-driven corrections are documented in
[docs/SOURCE-AUDIT.md](docs/SOURCE-AUDIT.md).
The final delivery review is in [docs/RELEASE-AUDIT.md](docs/RELEASE-AUDIT.md),
and the word-for-word video script is in [docs/LOOM-SCRIPT.md](docs/LOOM-SCRIPT.md).

Live application: https://farooqtrucks.vercel.app
Backup application: https://farooqtrucks.netlify.app
Source: https://github.com/farooq-abdullah/farooqtrucks

The Netlify backup serves the same React app and proxies `/api/` requests
to Django on Vercel. Use it if the Vercel hostname does not open on your network.
See [the access investigation and deployment notes](docs/ACCESS-REPAIR.md).

Delivery checks: 87 backend tests and eleven browser checks passed locally.
All eleven browser tests, two WebKit phone checks and 54 HTTP/API checks also
passed against the public app without signing in. Full evidence is in the
delivery review. The phone layout and interaction
corrections are documented in [docs/MOBILE-REVIEW.md](docs/MOBILE-REVIEW.md).

## No database required

The API calculates a plan and returns JSON. It has no accounts, sessions, saved
trips or database models. Django's database backend is explicitly disabled.
Provider results and request throttles use an in-memory cache, which disappears
when the server restarts. If saved trips are added later, use PostgreSQL.

## API

- `GET /api/health/`: service health and database status.
- `GET /api/locations/search/?q=Chicago`: cached place suggestions, including
  country/state labels and whether each result is in the supported area.
- `POST /api/trips/plan/`: validate inputs, resolve locations, obtain a road route,
  schedule duty events, and generate daily logs.

```json
{
  "current_location": "Chicago, IL",
  "pickup_location": "Springfield, IL",
  "dropoff_location": "St. Louis, MO",
  "current_cycle_used": 30
}
```

The API and UI use exactly the four required inputs. The backend infers an IANA timezone from the starting
location's coordinates and treats that location as a proxy for the home terminal.
It assumes the carrier's 24-hour log day begins at midnight. It uses the offset in
effect at departure throughout the trip to keep each planned sheet 24 hours; a
daylight-saving change during a trip is not modeled. FMCSA log time is based on
the driver's actual home terminal and carrier-specified day start, so these
assumptions may differ from a driver's real log settings.

Responses include resolved `locations`, `route` geometry and turn instructions,
timestamped `events`, `daily_logs`, a `summary`, `planning_parameters`, `clocks`
and `warnings`. React explains those returned parameters in its assumptions dialog.
Invalid input or an unsupported location returns 400; upstream map failures return a readable 502 error.
The UI also offers JSON download and printing of the planned log sheets.

## Scheduling assumptions

The assessment specifies a property-carrying driver, 70 hours / 8 days,
no adverse conditions, fuel at least every 1,000 miles, and "1 hour for pickup
and drop-off." We interpret the last item as one hour at each stop. The planner uses:

- Fresh daily clocks after at least 10 consecutive off-duty hours before departure.
- Up to 11 driving hours in a 14-hour elapsed window; midnight does not reset these.
- A 30-minute interruption after 8 cumulative driving hours. Consecutive
  non-driving activities of at least 30 minutes satisfy this rule, including loading
  and fueling. Short non-driving activities do not pause the 14-hour window.
- Driving and other on-duty work count toward the cycle allowance. The normal
  10-hour rest does not reset that cycle.
- The 70-hour cycle and 14-hour window restrict driving. Non-driving work can
  finish beyond those limits; capacity is checked before driving again.
- **No recapture of prior cycle hours:** the four inputs contain no previous daily
  history. The schedule conservatively retains the entered hours and uses a
  34-hour restart when capacity is insufficient. A 34-hour restart is optional under
  the actual rule; this planner chooses it rather than guessing when old hours expire.
  Consequently the trip can take longer than a plan based on complete history.
- A full tank initially; 30-minute fuel stops at or before every 1,000 miles.
- Pre-trip and post-trip inspections/TIV for each driving shift, estimated at
  15 minutes each. They count as on-duty time in the cycle and elapsed shift.
  The estimate is not a legal minimum or a record of a completed inspection.
- Departure today at 08:00 in the IANA timezone inferred from the starting
  coordinates. That location is treated as the driver's home terminal. The
  UTC offset in effect at departure stays fixed throughout this trip, so this
  version does not model a daylight-saving transition during the trip. If
  coordinate lookup fails, `LOG_UTC_OFFSET` supplies a fixed-offset fallback.
- Ten-hour and 34-hour rests are logged in the sleeper berth; the truck is assumed
  to have one. Short driving breaks are logged off duty, fueling/loading on duty.
- One driver, one carrier and the same tractor/trailer are assumed. Split-sleeper
  pairs, team changes, personal conveyance, yard moves and special exceptions are
  not modeled.
- Every calendar sheet is filled to 24 hours, including assumed off-duty time
  before departure and after completion. Events and mileage are split at midnight.

Reference: [FMCSA hours-of-service summary](https://www.fmcsa.dot.gov/regulations/hours-service/summary-hours-service-regulations).

These are predicted schedules, not actual ELD records. Driver/carrier/vehicle/
shipping information is not part of the supplied inputs and is left unspecified.

## Maps and remaining accuracy limits

- **Photon** provides suggestions and forward geocoding
  through Django. Its [public demo](https://github.com/komoot/photon#public-demo-server)
  permits reasonable project use without an availability guarantee. The UI waits
  350 ms after two characters, cancels stale requests and uses bounded timeouts.
  Exact-query browser and backend caches avoid duplicate searches; slow provider
  requests no longer hold a process-wide suggestion lock.
- Popular city abbreviations such as NY/NYC, LA, SF, DC, Vegas, CHI and STL
  expand to explicit city/state labels. A small bundled index contains real
  provider results with source IDs and retrieval dates, so common cities and
  demonstration routes resolve quickly without repeated upstream requests.
  A state suffix retains its meaning: `Baton Rouge, LA` means Louisiana.
  Other cities and addresses use live Photon. The provider can still take several
  seconds or fail; timeouts show a readable retry message.
- Set `LOCATION_SEARCH_BASE_URL` and `GEOCODING_BASE_URL` to your own Photon
  service for broader use. `GEOCODING_PROVIDER=nominatim` is an optional adapter
  for a compatible service; public Nominatim's application-wide one-request-per-
  second policy requires centralized coordination and is unsuitable as the
  default for independently scaling Vercel instances. Suggestions always use Photon.
- Search throttling and caches use per-instance memory. They are best-effort
  workload controls, not a distributed security or quota system.
- Forward searches are global, followed by country and contiguous-US checks.
  Thus Tokyo/Tokio resolves to Japan and is rejected, rather than automatically
  routing to its North Dakota namesake. Suggestions show the country and state,
  with unsupported places disabled. Free text still works; include a state or a
  full address to distinguish namesakes.
- **OSRM** returns a real road route and estimated durations, without live traffic
  or truck height/weight/clearance restrictions. A truck-specific routing provider
  should replace this adapter if those restrictions are required.
- Leaflet displays OpenStreetMap tiles with visible attribution. Both Django and
  the tile images use `strict-origin-when-cross-origin`, so tile requests send the
  app origin required by the [tile usage policy](https://operations.osmfoundation.org/policies/tiles/)
  without disclosing page paths or query strings. Browser caching remains enabled.
- The bundled 2026 [US Census Places Gazetteer](https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html)
  names estimated stop areas without a live reverse request. References such as
  “About 1 mi N of Lake Darby, OH” use the nearest published place reference point,
  approximate straight-line distance and direction. The itinerary adds the road,
  distance into the trip and a Maps link. These names identify areas, not facilities
  or highway mileposts. Dataset provenance is in
  [CENSUS-PLACES.md](backend/trips/services/routing/CENSUS-PLACES.md).
- Stop coordinates are interpolated along the road polyline from planned mileage.
  These are estimated break/fuel positions, not verified rest areas or fuel stations.
  Within each leg, mileage is distributed proportionally to elapsed driving time;
  varying speeds along individual road sections are not yet modeled.
- Remarks use city/state and available road references. Estimated coordinates
  and road names do not establish the actual rural milepost or named location
  needed for an official record.
- All resolved location names are displayed so ambiguous city/address matches can
  be checked. This version supports the contiguous US.
- Public demo services have no availability guarantee. Failures are surfaced;
  fabricated routes are never substituted.
  Read-only road requests retry a transient connection failure or 502/503/504
  once after a short delay; invalid data and rate-limit responses are not retried.

The 30-minute-break card reports separate stops scheduled during the trip and the
time of the first one, which can be opened on the map. Other driver-hour cards
show completion clocks. Unloading can reset the final break clock to zero; that
does not mean the preceding trip needed no breaks.

## Configuration and hosting preparation

See `backend/.env.example` and `frontend/.env.example`. Those files are references;
settings read the process environment, not `.env` files automatically.

For production set `DJANGO_DEBUG=false`, a strong `DJANGO_SECRET_KEY`, the actual
`DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and an identifying `MAP_USER_AGENT`
with your app URL/contact. Example on a Linux host:

```sh
cd backend
gunicorn config.wsgi:application --workers 1 --threads 4 --timeout 180 --bind 0.0.0.0:$PORT
```

The root `vercel.json` deploys both parts on one origin using Vercel's native
Django support. Vercel builds React, runs `collectstatic`, serves assets from its
CDN and runs the Django WSGI application as a Python function. Keep the project
root at the repository root, rather than `frontend/`; no separate backend host or
`VITE_API_BASE_URL` is required. Set production environment variables before
running `npx vercel deploy --prod`.

The `Dockerfile` and `render.yaml` remain alternative hosting options. A separate
frontend deployment can use `frontend/vercel.json` with `VITE_API_BASE_URL` set to
its Django origin and CORS configured accordingly.

## Verification

```powershell
.\.venv\Scripts\python.exe backend\manage.py check
.\.venv\Scripts\python.exe backend\manage.py test trips.tests
cd frontend
npm run build
npm test
```

The backend tests check location suggestions and country validation, HOS limits, cycle work accounting, inspections, loading as a qualifying break,
fuel mileage, midnight splits, 24-hour coverage, input validation, upstream errors,
and API responses without a database. They use mocked map data, so they do not
depend on public services or consume their quotas.
Eleven regressions from the complete source audit include the guide's page 19
totals, work beyond driving limits, mixed non-driving breaks, midnight positions,
separate adjacent activity details and full rest intervals across midnight.

The Playwright browser tests require both development servers to be running
and Microsoft Edge installed. They exercise real short and cross-country routes,
responsive layouts, errors, cancellation, downloads, multiple days, hover/focus
details, signature removal from the screen and export, PDF pagination, suggestion selection,
unsupported places, request debounce and stale search responses.
Automated rendering tests intercept background tiles with a neutral local SVG;
they do not fetch the public tile service. They verify the tile request's origin
referrer separately from the real route/API data. Actual basemap availability is
checked in a normal visible browser, separately from those rendering tests.
To use Playwright Chromium instead, install it with `npx playwright install chromium`
and set `$env:PLAYWRIGHT_CHANNEL='chromium'` before running `npm test`.
Set `PLAYWRIGHT_BASE_URL` to a hosted origin to run those same checks against
production. GitHub Actions validates Django, Ruff, the frontend build and the
time-format regression on pushes. The manual `Verify public deployment` workflow
checks the hosted API and runs Chromium and WebKit phone tests without Vercel
account cookies. To check phone layouts locally in WebKit, install it with
`npx playwright install webkit`, set `PLAYWRIGHT_BROWSER=webkit` and run
`npm test -- mobile.spec.js` from `frontend`.

After building, verify the production files from the repository root:

```powershell
.\.venv\Scripts\python.exe backend\manage.py collectstatic --noinput
.\.venv\Scripts\python.exe scripts\smoke-production.py
```

The smoke test uses production settings on port 8001 and checks the built HTML,
JavaScript, CSS, brand assets and API health. Docker's container build additionally
requires a running Docker daemon.

## How to read the Django code

Start with [docs/DJANGO-WALKTHROUGH.md](docs/DJANGO-WALKTHROUGH.md), which maps the
files and explains `manage.py` as the first lesson. Related functions stay together;
each module has a clear responsibility, and class methods remain with their class.

1. `manage.py` runs Django commands; `config/settings.py` configures the project.
2. `config/urls.py` and `trips/urls.py` send each URL to a view.
3. `trips/serializers.py` validates JSON; `trips/clock.py` handles the terminal clock.
4. `trips/views.py` connects routing, scheduling and log generation.
5. `trips/services/routing/` groups provider requests, geocoding, road routes and
   planned positions into separate modules.
6. `trips/services/hos/` separates the planning rules, driver state/operations and
   complete trip assembly. Its calculations remain independent of Django.
7. `trips/services/logs.py` produces each calendar day's log data.
8. `frontend/src/lib/assumptions.js` explains the backend's planning parameters.
9. `trips/tests/` groups tests by the behavior they verify.

`__init__.py` in the two service packages exposes their public functions and
classes. This keeps imports short while the implementation stays easy to locate.

Python formatting and import order are configured in `pyproject.toml`. Install
the development tools and check the backend from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m ruff format --check backend
```

The React entry point is `frontend/src/App.jsx`. `TripForm.jsx` collects the inputs,
`RouteView.jsx` and `RouteMap.jsx` show the returned plan, and `LogsView.jsx` plus
`LogSheet.jsx` display and print the backend's daily records. Calculations stay in Django.
