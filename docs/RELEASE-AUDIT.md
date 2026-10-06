# Delivery review — October 6, 2026

This review checks the employer's assessment against the delivered app. It records
concrete evidence and scope limits; passing tests does not establish accuracy for
every possible route or certify actual driver activity.

## Assessment checklist

| Requirement | Delivered behavior | Verification |
| --- | --- | --- |
| Django and React | Django/DRF API; React/MUI/Vite UI | Backend checks, production build, browser flow |
| Four inputs | Current location, pickup, drop-off, current cycle used | Serializer/API tests; accessible form |
| Route instructions | Two road legs with expandable turn instructions | Live OSRM and browser checks |
| Free map API | OSRM roads, Photon geocoding, attributed OpenStreetMap tiles | Provider adapters and live browser flow |
| Stops and rests on map | Selectable work, fuel, break and rest itinerary with markers | Short and cross-country browser tests |
| Filled daily logs | Four duty statuses, SVG traces, daily mileage, remarks, status totals | Daily coverage and conservation regressions |
| Multiple sheets | Split at midnight; select any day; print all days | Multi-day route and PDF page-count checks |
| Property driver, 70h/8d | 11h driving, 14h elapsed window, interruption after 8h driving, 10h rest, cycle constraint | Independent boundary and route/cycle sweeps |
| No adverse conditions | No limit extensions | Scheduler rules |
| Fuel at least every 1,000mi | Fuel at or before each interval; initial full tank assumed | Fuel spacing/boundary tests and long-trip flow |
| One hour for pickup/drop-off | One hour at each stop, counted as on duty | Schedule and hosted API checks |
| Good UI/UX | Responsive design, keyboard controls, loading/errors, route/log navigation | Desktop, tablet and mobile browser checks |
| Hosted version | Full app on Vercel, same-origin Django API and React assets | See public verification status below |
| GitHub code | Source, setup docs and CI | Repository link in SUBMISSION.md |
| 3–5 minute Loom | Complete ~4:40 script with screen directions | User records and adds resulting Loom URL |

## Corrections made during this delivery review

- Removed the driver's signature from the desktop/mobile sheet, printing, React
  state and downloaded JSON. Optional sheet metadata remains available.
- Reworked phone layouts after checking the supplied iPhone screenshots: compact
  header, bottom navigation, 16px inputs, smaller map markers, a full 24-hour
  overview and a 48px activity selector. [MOBILE-REVIEW.md](MOBILE-REVIEW.md)
  records the presentation regressions and preservation of exact schedule data.
- Fixed suggestion requests holding a process-wide lock during slow network I/O.
  Added connection reuse, exact-query caches, 350ms debounce, bounded waits and
  stale-response protection. UI timeouts stop the endless searching state.
- Added NY/NYC, LA, SF, DC and other city shorthand. Verified popular-city data
  supplies full city/state labels and coordinates without repeated upstream calls.
  `Springfie` returns distinct Springfields; a bare ambiguous Springfield requires
  a state when planning. `Baton Rouge, LA` retains Louisiana as its state.
- Switched default forward/reverse geocoding to Photon. Independently scaling
  Vercel instances cannot uphold the public Nominatim service's application-wide
  one-request/second policy with a process-local lock.
- Corrected the road reference on a drive continuing across midnight: it now
  resolves the road at the midnight position and leaves an unavailable road unknown.
- Reused resolved city/state labels at the current, pickup and drop-off endpoints
  instead of attempting unnecessary reverse lookups. Estimated intermediate stops
  still use optional reverse naming, with coordinates available on provider failure.
- Preserved nonzero seconds in detailed activity times; daily displayed totals
  explicitly use whole-minute allocation and add to 24:00. The recap uses those
  same displayed totals, while exported events retain exact integer seconds.
- Added provider-contract validation for non-finite/negative numbers, malformed
  coordinates, geometry, maneuvers and implausible duration/speed data. Invalid
  map responses produce a readable error instead of fabricated output or a hang.
- Rejected boolean cycle hours rather than silently treating true/false as 1/0.
- Upgraded DRF from 3.16.1 to 3.17.2 after the dependency audit found two published
  advisories. Pinned runtime requirements subsequently passed pip-audit.

## Validation record

- 79 Django tests passed, including API/provider boundaries, cycle/shift/break
  limits, inspections, fuel spacing, midnight continuation and exact-day coverage.
- Eleven Playwright checks passed locally against the restarted backend and current
  frontend: real short/cross-country routes, responsive layouts, errors, cancellation,
  signatures absent from UI/export, multi-day printing, shorthand and search timeouts.
- Both phone regression checks also passed in WebKit with mobile/touch emulation.
- Django system check, Ruff lint and formatting passed. React production build,
  static collection and the production-settings asset/API smoke test passed.
- Pinned backend requirements: pip-audit found no known vulnerabilities after the
  DRF correction. Frontend production dependencies: npm audit found zero.
- [GitHub CI](https://github.com/farooq-abdullah/farooqtrucks/actions/runs/37519689563)
  passed on Linux, including Django tests, Ruff, frontend build and time-format test.

The HOS regressions include two deterministic sweeps totaling 330 varied route/
cycle combinations, plus targeted limit and fractional-second boundaries.
The provider tests use mocked upstream payloads; live routing/browser checks
separately verify integration with real public services.

Measured on the restarted local API: NY 0–31ms, LA 31ms, Chicago IL 16ms, and
partial Springfield 0–16ms. These timings demonstrate the verified-city path;
they are not a guarantee of public network latency. A live Tokio search took
3.3s and correctly distinguished unsupported Tokyo from supported US results.
Photon's public service sometimes takes several seconds or times out. Other
addresses retain bounded, visible failures and retry behavior.

Independent final hosted measurements: NY 30ms, LA 32ms, SF 28ms. Short-trip
planning took 0.9s; the long Los Angeles/Dallas/New York case took 24.9s,
including road routing and optional stop naming. These are observations from
the saved hosted report, not latency guarantees. The long case is preloaded
in the Loom preparation so network wait does not consume the recording.

## Public verification status

Vercel production deployment `dpl_7FZQgdHHbDKSnEAuVgi1PiqAW4ph` reached READY at
https://farooqtrucks.vercel.app with the complete audit fixes. An initial runtime
import-path failure was corrected in the WSGI entry point; the React index and
city index are explicitly included in the Python function bundle.

The unauthenticated [public verification workflow](https://github.com/farooq-abdullah/farooqtrucks/actions/runs/37519823898)
passed all 49 HTTP/API checks: direct pages, built assets, health, NY/LA/SF searches,
short trip, exhausted cycle, long trip, stationary trip and invalid-input response.
All eleven browser tests also passed against the production URL, including desktop/
mobile views, route instructions, PDF pagination, signatures absent and search
timeouts. The two phone tests also passed in WebKit against production. The
complete hosted workflow passed in 2 minutes 55 seconds. Requests
used no Vercel cookies or bypass token; screenshots, PDFs and sample JSON plans
are downloadable from that run's `hosted-verification` artifact.

A repeat check caught a transient upstream Dallas lookup failure. Dallas is now
included in the verified city index with its original OpenStreetMap source ID;
the final long-trip API and browser checks passed. Short-trip endpoint remarks
retain Chicago, IL and Springfield, IL without reverse-lookup warnings.

This machine's home Wi-Fi path resets connections to vercel.app before HTTP.
The same Vercel IP responds when the hostname is nextjs.org, and the user
confirmed that the app opens on phone mobile data. GitHub's runner also reached
the public app successfully. The responsible router/ISP component remains
unidentified; changing the hosting plan does not resolve that filtering.
For recording on this connection, a mobile-data hotspot remains an access
workaround. The local UI is available at http://127.0.0.1:5180/plan.

## Accuracy scope reviewers should understand

- The four inputs cannot reconstruct prior seven daily totals. Old cycle hours
  are conservatively retained until a chosen 34-hour restart; exact recapture and
  tomorrow's rolling availability are unknown. A restart is a planning choice.
- The first shift starts today at 08:00 after an assumed ten-hour rest. The start
  location stands in for the home terminal, with a midnight log day and a fixed
  departure UTC offset. Daylight-saving transitions are not modeled.
- OSRM provides general road routes and estimated travel times, without traffic
  or truck height, weight and clearance constraints. Planned stop coordinates
  are positions along that route, not verified businesses or legal parking.
- Driver/carrier/vehicle/shipping information is unspecified unless the user adds
  optional sheet details. No names, historical duty activities or signatures are
  fabricated. Blank time outside the trip is assumed off duty.
- Inspection time (15 minutes per pre/post inspection), fueling time (30 minutes)
  and use of a sleeper berth for full rests are disclosed assumptions. One hour
  each for pickup and unloading follows the assessment interpretation.
- No split-sleeper, team-driver or special-exception mode is claimed. On-duty
  non-driving work can continue beyond driving limits; those limits prevent
  subsequent driving, rather than removing necessary unloading work.
- Per-instance caches/throttles are best-effort workload controls. Production
  scaling would need shared quotas/cache and a dedicated geocoder for guaranteed
  availability. This assessment app has no persistence or actual ELD certification.

References: [FMCSA HOS summary](https://www.fmcsa.dot.gov/regulations/hours-service/summary-hours-service-regulations),
[Photon public demo policy](https://github.com/komoot/photon#public-demo-server),
[Vercel Django deployment](https://vercel.com/docs/frameworks/full-stack/django),
[DRF 3.17.2 corrections](https://www.django-rest-framework.org/community/release-notes/#3172).
