# Assessment submission

- Hosted app: https://farooqtrucks.vercel.app
- Backup hosted app: https://farooqtrucks.netlify.app
- Source repository: https://github.com/farooq-abdullah/farooqtrucks
- Loom: record using [the complete script](LOOM-SCRIPT.md), then add your video URL.

This is a Django and React trip planner that accepts the four assessment inputs,
shows a road route and stop/rest schedule, and draws complete daily log sheets
for short and multi-day trips. Pickup and drop-off each take one hour. The
property-carrying 70-hour/eight-day mode does not use adverse-condition extensions.

Read [RELEASE-AUDIT.md](RELEASE-AUDIT.md) for the requirement-by-requirement check,
corrections, final verification record and accuracy scope. [SOURCE-AUDIT.md](SOURCE-AUDIT.md)
preserves the earlier review of the supplied guide and video. The driver's
signature has been removed as requested; these sheets describe a future plan.

## Recording and submission

The word-for-word [Loom script](LOOM-SCRIPT.md) runs about 4 minutes 45 seconds,
with exact screen actions, prepared examples and optional reviewer Q&A. The
[spoken-only copy](LOOM-READ-ALOUD.txt) is ready to use in a teleprompter.
Before recording, open the short Chicago/Springfield Illinois/St. Louis example
and preload the long Los Angeles/Dallas/New York example with 68 cycle hours.
Use actual output on screen rather than memorized mileage or times.

Paste these three links into the employer's submission question after recording:

1. https://github.com/farooq-abdullah/farooqtrucks
2. https://farooqtrucks.vercel.app
3. Your recorded Loom URL.

Suggested submission message:

> Hi Ena, here is my completed Django and React trip-planning assessment. The app
> generates a road route, a schedule of work, fuel stops and rests, and daily log
> sheets from the four required inputs. The GitHub README includes setup and
> verification instructions, and the walkthrough explains the app, code structure
> and planning assumptions. Links: [GitHub], [Hosted app], [Loom]. Thank you for
> reviewing my work.

## Hosting and reproducing checks

The Netlify backup serves the same frontend and proxies `/api/*` to the
existing Vercel Django deployment. The browser contacts Netlify for both
pages and API requests. See [ACCESS-REPAIR.md](ACCESS-REPAIR.md) for the
configuration and verification evidence. The backup currently uses a manual
deployment; source changes require a new upload or connecting the repository.

Vercel deploys from the repository root using native Django support. The root
vercel.json builds React, Vercel collects static assets for its CDN, and the
Python function runs config.wsgi.application. Both the frontend and API use the
same origin. No database, migration or map API key is required.

Set DJANGO_DEBUG=false, DJANGO_SECRET_KEY to a generated secret,
DJANGO_ALLOWED_HOSTS to your deployed hostname, and MAP_USER_AGENT to an
identifying application/contact value. The environment files are examples;
secrets remain in the host environment and are never committed.

Run backend/manage.py check, backend/manage.py test trips.tests, Ruff check and
format, then npm run build and npm test from frontend with both dev servers
running. Use PLAYWRIGHT_BASE_URL for production and PLAYWRIGHT_CHANNEL=chromium
on Linux after installing the Playwright browser. The manual GitHub Verify
public deployment workflow checks HTML, assets, the API and browser flows
without an account session; its artifacts preserve screenshots and sample plans.

The Dockerfile and Render blueprint are optional alternatives. Their container
build has not been verified locally; the submitted host is Vercel.
