# Mobile delivery review — October 6, 2026

The phone screenshots exposed a large sticky header, 14px inputs susceptible to
iPhone focus zoom, oversized overlapping map markers, and a horizontally cropped
daily log. The mobile workflow now has:

- A 60px brand/action header and fixed bottom navigation with safe-area padding.
- 16px inputs, clear location cues, consistent spacing and compact trip metrics.
- Numbered map endpoints, smaller intermediate dots, grouping only for identical
  coordinates, and labels on demand. Selecting an itinerary activity brings its
  map location into view; repeated selections reopen a dismissed popup.
- A complete 00:00–24:00 chart that fits the phone width. It uses the same exact
  schedule boundaries as the desktop and printed chart, with fewer axis labels.
- A labelled 48px activity selector so short inspections and adjacent activities
  can be inspected without tapping a tiny SVG segment. Timing, location, duration
  and reason retain their original precision.
- A clear “Clocks at completion” label and readable event/remark lists.
- Short CSS transitions, visible focus states and reduced-motion support.

The existing React/MUI stack, blue identity, desktop sheets and printed graph
remain in use. The HOS scheduler and API contract have not changed. The phone
form no longer mounts an unused hidden desktop map.

## Verification

The two new regressions first reproduced the 14px input and cropped-day defects.
The full suite also exposed a transparent transition intercepting the short
inspection target; compact transitions no longer intercept pointer events.
Separating the native select label fixed its accessible name.

- 11 browser checks passed against the final local source, including real short
  and long routes, mobile/tablet/desktop views, downloads and printed pagination.
- Both mobile regression checks passed in WebKit with touch/mobile emulation.
- 79 Django tests and the Django system check passed.
- React production build and production-settings HTML/assets/API checks passed.
- Independent code review rechecked the activity selector, repeated map focus
  and desktop layering; it reported no remaining actionable findings.

Phone layouts were checked at 320px, 390px and 430px. The deterministic mobile
tests use a recorded real API response; the other integration tests still call
the providers. WebKit emulation does not reproduce a physical iPhone's keyboard
or browser chrome. Safe-area behavior still benefits from checking on hardware.

Screenshots and hosted release evidence are captured by the public verification
workflow. Its WebKit step checks the same mobile regressions after deployment.
