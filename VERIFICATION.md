# Verification record

Verified locally on Windows on 2026-09-23. Mocked contract and browser tests are distinct from live provider checks.

## Automated checks

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q` | 175 passed |
| `npm.cmd test -- --run` (frontend) | 30 passed across 5 files |
| `npm.cmd run lint` (frontend) | Passed |
| `npx.cmd tsc --noEmit` (frontend) | Passed |
| `npm.cmd run build` (frontend) | Passed; production pages and API routes generated |
| `git diff --check` | Passed |

The Python suite emits one upstream Starlette warning about the TestClient HTTP transport's future migration. It does not fail tests.

Coverage includes local-model connection errors, malformed output, rejected monetary fields and invented place references; provider failures, empty discovery, cache expiry, retries, rate limits, missing credentials, partial/out-of-range forecasts and unknown opening hours; hotel room totals, explicit exchange rates, incomplete and infeasible budgets, expense accounting; lock/completion preservation, failed replans, timezone retention, restart recovery, revision history, and stale-version conflicts.

## Browser and production checks

The full browser flow used the explicit `tests/browser_server.py` harness, a temporary database, and test-only provider/model fixtures. No fixture server is part of normal startup.

- Created a dated Jaipur trip, opened its daily itinerary, and locked an activity.
- Recorded a food expense and verified its budget accounting.
- Used the test model response to change activity pace.
- Changed the test weather feed and advanced the harness clock past the monitoring interval. The backend automatically revised the itinerary, retained the locked activity, and recorded an explained before/after revision.
- Observed the visible browser update through its 30-second polling cycle.
- Paused monitoring, reloaded the page, and verified saved preferences, expenses, itinerary, and monitoring state.
- Inspected the interface at desktop size and a 390 x 844 mobile viewport; reset the temporary viewport afterwards.

After stopping the harness, ran `next start` against the normal backend. The production planner rendered correctly; its health, trip-list, and capability proxy endpoints returned HTTP 200. The normal database returned an empty trip list. The missing-model conversation request returned the actual configuration error with HTTP 503. No seeded trips remain in the delivered application.

## Live integration checks and limits

| Service | Observed result |
| --- | --- |
| Open-Meteo geocoding | Live Jaipur lookup succeeded, including Asia/Kolkata timezone |
| Open-Meteo weather | Live three-day forecast succeeded |
| OpenStreetMap / Overpass | Public default endpoint returned HTTP 504; an alternate public instance timed out. Failure handling was exercised; successful live discovery was not verified in this environment. |
| Local model | No model identifier/server configuration available; inference was not live-tested. Connection/error/structured-output handling passed mocked tests. |
| Amadeus production hotels | Credentials unavailable; production offers were not live-tested. Contract and missing-credential tests passed. |
| TomTom routing/traffic | Credentials unavailable; live routing/traffic were not tested. Contract and missing-credential tests passed. |

The application's ability to generate a useful live itinerary depends on successful place discovery. Provider outages remain visible instead of substituting fabricated places. Form planning does not require a model. Hotel prices and traffic remain unavailable until their providers are configured.

No model runtime or weights were installed or downloaded, no model-load calls were sent, and no commits were pushed or published. All sample CSVs are isolated under `tests/fixtures`.

## Milestones

The four local commits follow the agreed implementation milestones at 30%, 50%, 75%, and 100%. Upstream repository history is preserved. Setup and operating limitations are documented in [README.md](README.md) and [docs/GUIDE.md](docs/GUIDE.md).
