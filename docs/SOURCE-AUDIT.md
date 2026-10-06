# Complete assessment source audit

Reviewed on October 5, 2026. This records the sources, their application to the
assessment, the corrections made, and the limits of the four-input planner.

**Delivery update, October 6, 2026:** this document preserves the earlier source
review. The final app removes the driver signature on the user's instruction,
uses Photon and a verified common-city index for geocoding, and includes the
Vercel deployment. See [RELEASE-AUDIT.md](RELEASE-AUDIT.md) for current evidence.
The guide's signature requirement concerns actual records; this app generates
future plans and does not certify completed driver activity.

## Sources and review method

- Read the complete attached `new-full-stack-dev-assessment.docx`.
- Read every page of the attached April 2022 FMCSA *Interstate Truck Driver's
  Guide to Hours of Service*: **27 PDF pages**, including the appendix of exceptions.
  Visually checked the split-sleeper example on page 8, the rolling-cycle table on
  page 11, and the completed log on page 19. Source SHA-256:
  `FB494DB56E1D22F0C88311C351C78CD8F18C5565B066CBD7B21D1E7267E3B494`.
- Retrieved and read the **complete available automatic transcript** of
  [Schneider's 6:46 logbook walkthrough](https://www.youtube.com/watch?v=whxe41XYXS8),
  from the introduction through the closing. Inspected the video examples of the
  header, inspection form, graph, remarks and status totals. This was a transcript
  and visual-example review, not uninterrupted viewing of every frame. Automatic
  captions contain errors; visible labels resolve the TIV terminology.
- Compared the core scheduling and recordkeeping rules with the current
  [FMCSA summary](https://www.fmcsa.dot.gov/regulations/hours-service/summary-hours-service-regulations),
  [49 CFR 395.3](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-III/subchapter-B/part-395/subpart-A/section-395.3),
  and [49 CFR 395.8](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-III/subchapter-B/part-395/subpart-A/section-395.8).
  The eCFR pages reviewed showed Title 49 current through October 1, 2026.

Extracted guide pages, the transcript and visual inspection files are private
working material under ignored `artifacts/source-audit/`. This report summarizes
them; it does not republish the guide or full transcript. Appendix exceptions were
read to check scope, not adopted as additional modes for this assessment.

## What the employer actually requests

| Requirement in the assessment | App status |
| --- | --- |
| Django + React | Django/DRF calculation API and React frontend. MUI follows the user's additional instruction; the DOCX itself does not name MUI. |
| Current location, pickup, drop-off, current cycle used | Exactly four required UI inputs, validated by the API. |
| Route and stops/rests using a free map API | Nominatim, OSRM and attributed OpenStreetMap tiles; route instructions and scheduled stops on the map. Stop positions are estimates, not verified businesses or parking facilities. |
| Drawn, filled daily log sheets | Four status rows, 24-hour graph, totals, daily mileage, remarks and optional header details. |
| Multiple sheets for long trips | Events and mileage split at terminal-clock midnight; day selection and printing all days. |
| Property-carrying, 70 hours / 8 days | Daily driving, shift, break and cycle rules; conservative restart policy when history is unavailable. |
| No adverse conditions | No adverse-condition extensions. |
| Fuel at least every 1,000 miles | Fuel stops at or before that mileage interval, starting with an assumed full tank. |
| "1 hour for pickup and drop-off" | Interpreted as one hour at each stop; on-duty work events, one hour each. |
| Good design and UX | farooqtrucks design, responsive views, working navigation, input/error/loading states. |
| GitHub, hosted version and 3–5 minute Loom | Local code and deployment preparation exist. Publication, hosted verification and recording remain pending. |

The emailed assessment allows four days and sixteen work hours. Neither the
DOCX nor this logbook video requires live GPS tracking, a custom shortest-path
algorithm, accounts or a database. A company's sample form in the video includes
a Canadian cycle label; the assessment's explicit US **70-hour / 8-day** scope
controls this implementation.

## FMCSA guide: complete page coverage

Page numbers below are the physical PDF pages, matching the numbered body pages.
"Outside scope" means the content was reviewed but is not a requested mode.

| Page | Content reviewed | Application to this app |
| --- | --- | --- |
| 1 | Cover, publication identity and April 2022 date. | Identifies the supplied source version. |
| 2 | Contents and revision notice replacing older guidance. | Read the complete body and appendix; do not use older rules by default. |
| 3 | HOS purpose, guidance status, CMV definition and property/passenger scope. | Property-carrying assessment mode; no passenger-service limits. |
| 4 | Interstate/intrastate commerce, empty-truck operation, prior seven-day history and personal conveyance. | Prior history is unavailable; personal conveyance and jurisdiction classification are outside the planner's inputs. |
| 5 | Yard moves and on-duty work, including inspections, fueling, loading, other employment and required activities. | Inspections, fuel, pickup and unloading count as on duty. Other work and yard moves are not invented. |
| 6 | Off-duty conditions, parked vehicle rest, team passenger time, fresh ten-hour rest, fourteen-hour window and eleven driving hours. | Fresh daily clocks assumed; 11/14 limits enforced before driving. OFF means released from work. Team operation is outside scope. |
| 7 | Sleeper berth use: full rest, combined rest and qualifying split periods. | Full rests use an assumed actual sleeper berth. Split-sleeper scheduling is not implemented or claimed. |
| 8 | Two-day split-sleeper graph and four rest periods. | Visually reviewed; checked that ordinary breaks are not incorrectly treated as split-sleeper pauses. |
| 9 | Paired sleeper examples and driving/window recalculations. | No split-pair calculation. Non-driving work can continue after the driving window expires. |
| 10 | Thirty-minute break after eight accumulated driving hours, mixed non-driving breaks, 60/70-hour limits and rolling days. | Consecutive ON/OFF/SB periods can satisfy the break. A short break does not pause the fourteen-hour window. Cycle restrictions apply to driving. |
| 11 | Rolling-cycle table, seven/eight-day schedules and optional thirty-four-hour restart. | Visually checked the table. Midnight does not erase cycle usage; no exact recapture without daily history. A 34-hour restart is a planner choice when further driving needs capacity. |
| 12 | Adverse-condition extension and CDL short-haul exception, including manual/ELD thresholds. | Adverse and short-haul exceptions are excluded from this assessment mode. |
| 13 | Short-haul time records and non-CDL conditions. | No short-haul exception or employer time-record system is claimed. |
| 14 | Sixteen-hour exception and ordinary log/ELD obligations. | No sixteen-hour extension. Generated plans are not certified ELD records. |
| 15 | Date, driving mileage, vehicle identification and log header/grid. | Dated sheets, driver and truck mileage, optional tractor/trailer identification. Mileage is predicted, not an odometer reading. |
| 16 | Carrier/main office, signature, co-driver, home-terminal clock, remarks, totals and shipping details. | Optional metadata, unsigned signature line, origin-inferred terminal clock, shipping fields and four totals. Missing values are visible. |
| 17 | Four status lines and locations of changes; rural highway/milepost or named location requirements. | All four statuses and duty-change remarks. Structured city/state and available road names are used; estimated rural positions still need actual record details. |
| 18 | Richmond-to-Newark worked example, including unloading beyond the fourteen-hour driving window. | Checked the distinction between prohibited driving and permitted non-driving work. |
| 19 | Completed log graph/header, twenty-four-hour totals, submission/retention and multiple carriers. | Visually checked; added an independent totals regression. No signature certification, carrier submission or statutory retention service is supplied. |
| 20 | Appendix: detailed CDL and non-CDL short-haul conditions. | Read; outside the ordinary interstate property mode. |
| 21 | Appendix: adverse conditions, agricultural operations and covered farm vehicles. | Read; no automatic agricultural/farm exemptions. |
| 22 | Appendix: Alaska limits and construction-material/equipment rules. | Read; Alaska excluded by the contiguous-US planner, construction exception not selected. |
| 23 | Appendix: manual/ELD exceptions, driver-salespersons, emergencies and federal government. | Read; the app does not determine ELD exemption eligibility or emergency relief. |
| 24 | Appendix: fire/rescue, groundwater drilling, Hawaii, local government, movie/TV and oilfield operations. | Read; these alternate rules are outside scope. |
| 25 | Appendix: personal property, propane emergencies, railroad signals, retail deliveries, school buses, sixteen-hour and state-government exceptions. | Read; no such exemptions are inferred from a route. |
| 26 | Appendix: emergency towing and utility-service vehicles. | Read; ordinary limits remain active. |
| 27 | FMCSA contact information. | Source contact page reviewed; no additional app behavior. |

### Two rules that required particular care

1. **70 hours restricts further driving.** Loading, unloading and inspections may
   continue beyond that total. They still count as on-duty time. Before driving
   again, the driver needs sufficient cycle capacity through recapture or restart.
2. **34 hours is optional under the rule.** The planner lacks the previous daily
   hours needed to predict recapture. It retains the supplied total and schedules
   a restart when necessary for the next drive. That can produce more rest than
   complete history would require. A new calendar day alone is not a reset.

The same driving/work distinction applies to the fourteen-hour window. The
independent regression based on the page 19 graph accounts for **10:00 OFF,
1:45 SB, 7:45 driving and 4:30 ON**, totaling 24:00. That fixture follows the
supplied illustration, including its unloading interval.

## Video: complete content comparison

| Approximate timestamp | Content | App treatment |
| --- | --- | --- |
| 0:00–0:23 | Introduction to paper logs. | Planned daily-log output, with explicit unsigned status. |
| 0:24–0:49 | Date, full twenty-four-hour grid, hours and fifteen-minute ticks. | Dated midnight-to-midnight graph, hourly labels, quarter-hour ticks, explicit Midnight/Noon labels. |
| 0:50–1:23 | OFF, sleeper berth, driving and ON; sleeper berth describes the driver's physical location. | Four rows. SB is assumed only for full rests in an actual berth; the assumption is visible. |
| 1:24–1:44 | Remarks include places and activities such as inspections, load/unload, trailer changes and fuel. | Locations and scheduled activities; no fictional scale, trailer-change or en-route inspection events. |
| 1:45–2:23 | Date, driver number, initials, signature, co-driver, terminal, vehicle and load information. | Optional driver ID/initials and remaining header fields; missing details not fabricated; signature remains blank. |
| 2:24–3:35 | OFF to 06:30; thirty-minute pre-trip/TIV in Green Bay; connected trace and stationary remark brackets. | Pre-trip inspection/TIV before driving, connected status trace and explicit location remarks. App departure is assumed 08:00 and inspection duration 15 minutes, not copied from the sample. |
| 3:36–4:09 | Thirty-minute scale stop in Fond du Lac, then driving. | Demonstrates ON for required work. A scale stop is not inferred for every trip. |
| 4:10–4:46 | Thirty-minute off-duty break at Paw Paw, then driving. | Break scheduling after eight accumulated driving hours; earlier qualifying load/fuel periods also satisfy the rule. |
| 4:47–5:12 | Edwardsville post-trip/TIV, then off-duty time and sleeper berth. | Post-trip/TIV before a full rest or final completion; inspection work is logged ON. No actual inspection findings are generated. |
| 5:13–5:35 | Driving mileage versus total truck mileage, particularly for co-driving. | Separate labels show the same estimated mileage under the disclosed solo-driver assumption. |
| 5:36–6:21 | Totals: 8:30 OFF, 5:00 SB, 9:30 driving, 1:00 ON; 24:00 total and 10.5 hours on duty. | Each sheet totals 24:00; cycle work equals driving plus ON, with H:M formatting. |
| 6:22–6:46 | Closing and music. | No additional functional requirements. |

**TIV means Trailer Integrity Verification.** The complete review confirms it
belongs to inspection activity, not a fifth duty status. The video shows a
thirty-minute pre-trip sample and a six-minute post-trip note. The app's fifteen
minutes each are planning estimates, not statutory minimums.

The video sample's six-minute post-trip note is not allocated to line 4 in its
displayed totals. The app counts **every scheduled inspection minute as on duty**;
it does not reproduce that accounting omission. A visual inspection report shown
in the video contains findings/certification fields. Planning alone cannot fill
those truthfully, so the app does not assert that an inspection happened or that
no defects were found.

The video description emphasizes paper backup for ELD failure. The guide also
describes other manual-record exceptions. The app does not determine which
recording method a real driver is legally allowed to use.

## Corrections made after this review

1. Removed an unnecessary **34-hour delay before unloading** when cycle capacity
   was nearly exhausted. Non-driving work now finishes; capacity is checked before
   the next drive. Completion cycle usage can exceed 70, with zero driving budget.
2. Corrected **midnight continuation remarks**: a truck moving at midnight gets
   its estimated position along the actual route polyline, not the earlier town
   or a straight-line interpolation between endpoints.
3. Preserved structured **city and state** when users enter a street address;
   full provider labels remain available for checking the resolved destination.
4. Retained available **road names/references** for estimated stop remarks.
   A road name plus approximate coordinates still does not establish a verified
   rural milepost, parking location or facility.
5. Added optional **driver number and initials**, and a separate **truck-mileage**
   label for the solo-driver estimate.
6. Clarified sleeper-berth, single-driver/vehicle/carrier, missing-history and
   outside-trip OFF assumptions. Relabeled recap B as a planned day-start budget;
   exact prior-seven-day and next-day recap values remain unknown.
7. Adjusted print spacing and metadata columns after the expanded header caused
   long-trip sheets to spill onto a second page. Both restart and cross-country
   print checks now produce one page per day.

Relevant implementation: `backend/trips/services/hos/`, `routing/`, `logs.py`,
`backend/trips/views.py`, `frontend/src/LogSheet.jsx`, and the help/clock components.
Independent examples and regressions are in
`backend/trips/tests/test_source_audit.py`.

## Remaining limits, kept visible

- **Earlier daily hours:** one aggregate cycle value cannot identify which hours
  will expire on which day. The accepted four-input planner uses a conservative
  restart policy; exact rolling recapture is unavailable.
- **Initial daily state:** assumes an 08:00 departure after a qualifying ten-hour
  rest. It does not know actual work or driving earlier that day.
- **Terminal clock:** infers an IANA timezone from the starting coordinates and
  treats the start as the home terminal. The offset in effect at departure remains
  fixed through the trip to preserve 24-hour sheets; daylight-saving transitions
  during a trip are not modeled. An optional terminal text value does not select
  the timezone. The driver's actual home-terminal standard controls official logs.
- **Routing and stop suitability:** OSRM supplies general road directions and
  estimates, without truck restrictions, traffic or verified fuel/parking sites.
  Driving time is distributed proportionally within each route leg.
- **Operation:** assumes one driver, one carrier, the same tractor/trailer and a
  sleeper berth. No split-sleeper pairs, team changes, personal conveyance, yard
  moves or special exceptions. Extra scales, delays, trailer changes and actual
  inspection findings require information not supplied by the four inputs.
- **Official records:** generated sheets are predictions, with assumed OFF time
  outside the trip and estimated mileage. An optional typed name applies only
  to the selected day; it does not certify planned activity or create certified
  ELD records. Actual duty-change locations, vehicle changes, other employment,
  carrier submission and statutory retention are not managed. No database is
  required for this stateless assessment planner.
- **Submission:** GitHub publication, hosting and the Loom video still need to
  be completed. Local preparation is not a submitted hosted assessment.

## Verification

- **42 backend tests**, including eleven source-audit regressions and a sweep of
  150 route/cycle combinations. Includes the independent page 19 totals, mixed
  qualifying breaks, work beyond driving limits, restarts before subsequent
  driving, street-address city/state, road remarks, moving-midnight positions,
  separate adjacent activities and full rest intervals across midnight.
- **Four browser scenarios:** real short route; validation/provider errors/help/
  cancellation; full-cycle restart with multiple days and metadata; cross-country
  fuel/rest planning. Responsive widths and one printed page per daily sheet are
  included. The print regressions were rerun after fixing the overflow.
  Timeline hover/focus details and per-day typed names in mobile, print and JSON
  output are also verified. Scheduling reasons distinguish daily driving,
  elapsed-window and cycle rest triggers.
- Production frontend build, Django checks/static collection, and a production
  WSGI smoke check of HTML, JS/CSS, SVG assets and API health.
- Container build is still unverified because the local Docker daemon was
  unavailable. Public map results and production hosting depend on their providers.
