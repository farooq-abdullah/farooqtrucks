# Loom walkthrough — farooqtrucks

Target: about 4 minutes 45 seconds at a calm pace. Read only the **Say** paragraphs. The action notes, preparation and Q&A are not spoken. Pause briefly after changing screens; avoid scrolling while explaining a rule.

## Recording links and verified release checks

- Live app: `https://farooqtrucks.vercel.app`
- GitHub repository: `https://github.com/farooq-abdullah/farooqtrucks`
- Release checks, as one spoken phrase: `seventy-nine backend tests, nine browser tests, formatting checks and the production build`

The tests above passed locally; the same nine browser checks also passed against the public Vercel app without signing in. The full evidence and assumptions are in `RELEASE-AUDIT.md`.

## Preparation

1. Open the hosted app at `https://farooqtrucks.vercel.app` in two tabs. Use a clean browser window with unrelated tabs, notifications and secrets out of view. Keep the address bar visible at the introduction.
2. In the first tab, prepare **Chicago, IL → Springfield, IL → St. Louis, MO**, with **20** current cycle hours. Select the Illinois result for Springfield. Leave this tab on **Plan trip** with the four inputs visible.
3. In the second tab, generate **Los Angeles, CA → Dallas, TX → New York, NY**, with **68** current cycle hours. Verify the resulting plan actually shows fuel stops, a cycle restart and multiple log days. Preload it so provider latency does not consume the recording.
4. In the editor, open `backend/trips/views.py`, `backend/trips/serializers.py`, `backend/trips/services/hos/planner.py`, `backend/trips/services/logs.py`, and the test folder. Keep the `services/routing` folder visible in the file tree. Do not open `.env` files.
5. Keep a terminal showing the final successful backend and browser test summaries. The spoken test summary must match these results. Open the repository link in another tab for the closing shot.
6. Rehearse once. At 130–145 words per minute, the spoken script plus short screen transitions fits the assessment's 3–5 minute window. Read the output currently on screen; avoid adding memorized mileage, arrival times or day counts.

## 0:00–0:25 — Introduce the delivered app

**On screen:** Show the hosted app's address bar, then the complete four-field form. Keep the cursor still.

**Say:**

Hi, I'm Farooq. This is farooqtrucks, my Django and React trip planner. It takes the driver's current location, pickup, drop-off and current cycle hours, then produces a road route, a stop schedule and daily log sheets. I'll demonstrate a short trip, a longer trip that needs rest and fueling, and the code and tests behind the calculations.

## 0:25–1:15 — Show the normal workflow

**On screen:** Point briefly to the four prepared inputs. Click **Plan route & logs →**. Once the route loads, show the summary, click a stop to focus the map, then expand the **Chicago → Springfield** road leg. End by clicking **Review log sheets →**.

**Say:**

For the first example, I'm starting in Chicago, picking up in Springfield, Illinois, and delivering to St. Louis, with twenty cycle hours already used. Location suggestions include the state so similarly named places are distinguishable.

The result shows the route, estimated distance and driving time, and a chronological itinerary. Selecting an activity focuses its location on the map. Expanding a road leg reveals the driving instructions. The map uses OpenStreetMap tiles, with OSRM supplying the general road route.

Pickup and drop-off each take one hour. The plan also includes fifteen-minute inspections as an explicit planning estimate. Completion includes unloading and the final inspection, so it is different from simply arriving at the destination.

## 1:15–2:05 — Explain the log sheets accurately

**On screen:** On **Daily logs**, show the four-status graph. Hover over the pickup activity, then scroll to remarks and the recap. Briefly click **Print logs**, show the print preview, and cancel it.

**Say:**

The daily sheet draws off duty, sleeper berth, driving and on-duty time across a full twenty-four hours. Hovering over an activity explains its timing and why it exists. Remarks retain seconds when needed; displayed totals are rounded to minutes and still add up to twenty-four hours.

The important distinction is that midnight starts a new sheet, not a new driving shift. The scheduler carries shift and cycle usage across midnight. It applies the rest rules before resetting them.

The recap also avoids inventing history. We know the entered cycle usage, but not the previous seven daily totals, so exact rolling availability is marked as unavailable. Print generates a separate sheet for each planned day.

## 2:05–3:05 — Show the demanding case and its assumptions

**On screen:** Switch to the prepared Los Angeles → Dallas → New York tab. Show the **68**-hour input briefly through **Edit trip**, then click **Back to the previous plan →**. Scroll through the itinerary to a fuel stop and a **34-hour restart**. Open **Planning assumptions**, then show the multiple daily-log choices.

**Say:**

This longer example starts in Los Angeles, picks up in Dallas, and ends in New York with sixty-eight cycle hours already used. It exercises fueling, overnight rest and a cycle restart rather than just a short daytime drive.

The scheduler accounts for eleven driving hours, the fourteen-hour driving window, and a qualifying thirty-minute interruption after eight accumulated driving hours. It schedules fuel at or before each thousand-mile interval and applies the seventy-hour cycle constraint. Without earlier daily history, it uses a thirty-four-hour restart when more cycle capacity is needed.

These are planned outputs under stated assumptions. The start location supplies the assumed home-terminal clock, with a fixed UTC offset. Road times and stop positions are estimates; the route does not validate truck restrictions or identify verified parking. This is a planning tool, not a certified ELD.

## 3:05–4:20 — Show the architecture and evidence

**On screen:** Switch to the editor. Show `views.py` and the serializer first. In the file tree, point to `services/routing`, then show the scheduling loop in `services/hos/planner.py` and the midnight split in `services/logs.py`. Finish on the successful test summaries and their corresponding test files.

**Say:**

On the backend, the Django view coordinates the request. The serializer validates required locations and rejects non-finite cycle hours or values outside zero to seventy. Routing, scheduling and log generation live in separate services, so the rules can be tested without calling a map provider. WSGI is the server entry point; the trip logic belongs here in the services.

The scheduler uses integer seconds. The log service splits events at midnight without changing their meaning. React presents that returned schedule rather than implementing a second set of driving rules.

The recorded release checks passed: seventy-nine backend tests, nine browser tests, formatting checks and the production build. They cover limit boundaries, cycle restarts, fueling intervals, midnight crossings, twenty-four-hour totals, input errors, responsive views and printing.

Boundary tests replay events and assert the limits at every driving segment, rather than trusting output labels. Browser checks then verify that users see the same schedule on desktop, mobile and printed pages. This checks both the calculation and its presentation.

Location search also has bounded waits, caching and stale-response protection. A failed provider request produces a visible error rather than a fabricated route.

## 4:20–4:40 — Close

**On screen:** Show the hosted app once more, then the GitHub repository. Leave both links in the Loom description, alongside the assessment submission.

**Say:**

The main engineering challenge was keeping the route, schedule and daily sheets consistent while making the assumptions visible. The hosted app and source repository are linked below, with setup instructions and the verification record. Thank you for reviewing my work.

## Optional reviewer Q&A — outside the timed script

**Why Django and React?** Django REST Framework validates requests and exposes the planning API. React handles the form, map, itinerary and printable SVG log charts. Scheduling rules remain on the server.

**What happens at midnight?** The log renderer clips the same schedule into calendar-day sheets. Midnight alone resets neither the eleven-hour driving allowance nor the fourteen-hour window nor the cycle.

**Can the exact eight-day recap be computed from one cycle number?** No. Daily history determines which old hours expire. The app leaves missing history unspecified and uses a disclosed restart strategy, which can schedule more rest than a full historical recap would require.

**Why can total on-duty work exceed seventy hours?** The standard rule limits further driving after the cycle threshold. Non-driving work can finish beyond it. The scheduler must prevent subsequent driving until capacity is restored; it must not silently omit unloading or inspections.

**Why show seconds in some times but rounded daily totals?** Internal schedule boundaries retain integer-second precision. The detailed UI preserves those boundaries, while the sheet allocates rounded minutes across statuses to keep the displayed total at exactly twenty-four hours. The UI labels that rounding.

**Does the app certify a legal or truck-safe trip?** No. It plans under the assessment's property-carrying, seventy-hour/eight-day assumptions without adverse-condition exceptions. General road routing lacks truck restriction validation, stops are estimated, missing history is not reconstructed, and daylight-saving changes during a trip are not modeled.

**Why no database?** The required workflow calculates a plan from a request and returns it. Persistent accounts or trip storage are outside this assessment. Downloaded JSON preserves the generated plan and optional sheet details; refreshing starts a new in-memory session.

**What would you improve next?** Add actual prior daily duty history, a carrier-configured home-terminal clock, verified truck routing and stop facilities, and persistent trip records if those became product requirements. Keep each addition covered by independent scheduling invariants and end-to-end checks.
