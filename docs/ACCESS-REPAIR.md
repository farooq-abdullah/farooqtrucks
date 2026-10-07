# Public access investigation - October 7, 2026

Some Wi-Fi connections close HTTPS connections to `farooqtrucks.vercel.app`
before receiving an HTTP response. The user's hotspot and an independent
Android Wi-Fi test can open the app; an iPhone on another Wi-Fi network cannot.
Those observations do not identify the router or ISP responsible.

## Evidence

- Vercel reports production deployment `dpl_3ScZvqLkTqDvVx5ycowhJzwwn2Df`
  as Ready, aliased to `farooqtrucks.vercel.app`.
- On the affected local connection, curl reports a connection reset for the
  production domain, its alternate Vercel alias and an unrelated Vercel app.
- Forcing the production hostname to `216.198.79.3` still resets the connection.
  The same IP responds with HTTP 200 when addressed as `nextjs.org`. Changing
  DNS alone therefore did not resolve the observed failure. This points to
  hostname-dependent connection handling; it does not identify who closes it.
- A fresh unauthenticated GitHub-hosted verification of current commit
  `7699d2a793156bad968dfa0eac750da5c49e6b27` completed successfully:
  [verification run](https://github.com/farooq-abdullah/farooqtrucks/actions/runs/37548827940).
  It passed the HTTP/API smoke checks, all eleven Chromium browser tests,
  and both WebKit phone checks.

## Published workaround

Backup URL: https://farooqtrucks.netlify.app

Published on October 7, 2026 using Netlify Drop. Project ID:
`6ab7238a-784e-45f9-87fa-9414591dc154`. Production is public; deploy previews
remain private. The optional hosting badge is disabled to retain the app's
existing appearance.

`netlify.toml` serves the current React build on Netlify and proxies `/api/*`
to the existing Vercel Django API. Browsers use the Netlify origin for both
pages and planning requests. API requests must remain relative; a direct
Vercel `VITE_API_BASE_URL` would reintroduce the affected connection path.

Direct `/plan`, `/route` and `/logs` navigation falls back to `index.html`.
The referrer policy is retained so OpenStreetMap tile requests receive the
origin referrer required for the deployed map.

On the previously affected local connection, the new origin passed all 54
public HTTP/API checks, including short, long, exhausted-cycle and
same-location plans. Long-trip planning completed in about 2.4 seconds.
The browser also generated the sample Chicago–Springfield–Saint Louis route
through the new origin. Independent browser verification is recorded below.

[Independent Netlify verification](https://github.com/farooq-abdullah/farooqtrucks/actions/runs/37549974632)
completed successfully on October 7, 2026 at 03:06 Asia/Amman. It passed all
54 public HTTP/API checks, all eleven Chromium browser tests (42.2 seconds),
and both WebKit phone checks (7.2 seconds). These checks use the public backup
URL without Netlify login cookies. No backend source change was needed.

This fixes the connection path tested here; it does not guarantee every
network's access or establish DNS as the original cause.

The existing Vercel deployment remains the API origin. Slow upstream requests
can be subject to Netlify's proxy timeout; check the short and long trip API
flows after publishing. This approach does not move the Django backend.

## Deployment and verification

For a Git-connected Netlify project, use this repository's root directory.
The root `netlify.toml` installs and builds `frontend`, publishes
`frontend/dist`, and defines the API proxy before the React fallback.
Keep `VITE_API_BASE_URL` empty in Netlify's environment settings.

The prepared manual-upload archive is `farooqtrucks-netlify.zip` in the
user's Downloads directory. It contains the frontend build at its root,
plus `_redirects` and `_headers` with the same proxy and header settings.
It contains no backend source or environment secrets. A manual deployment
is a snapshot; subsequent source changes require another upload or a
Git-connected deployment.

After Netlify provides its public URL:

1. Open `/plan`, `/route`, and `/logs` directly to verify React navigation.
2. Verify location suggestions and generate a short trip and a long trip.
3. Confirm the browser uses the Netlify `/api/` paths for those requests.
4. Run the **Verify public deployment** GitHub Actions workflow with the
   Netlify origin as its `url` input. This checks public HTTP/API responses,
   the Chromium browser suite, and the WebKit phone layouts.
5. Record the actual URL and results here before sharing the backup link.
