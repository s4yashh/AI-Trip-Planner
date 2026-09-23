# Configuration, architecture, and behavior

## Run locally

Follow the root README. The backend loads the root `.env`; restart after changing it. The frontend's optional `.env.local` sets `AI_BACKEND_URL`. Bind both services to loopback. Run one backend worker for this single-user application.

The development script uses Webpack because the tested Windows/Turbopack development combination returned 404 for catch-all API routes. Production uses the standard Next.js build. System fonts avoid build-time downloads.

## Assistant provider: local or Gemini

Set `LLM_PROVIDER=local` (the default) or `LLM_PROVIDER=gemini`. Provider selection is explicit: a failed local connection never sends your conversation to Gemini automatically. Restart the backend after configuration changes and reload the page. The assistant panel displays the selected provider and setup instructions.

### Gemini

Add these values to the root `.env`, which is ignored by Git:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-google-ai-studio-key
GEMINI_MODEL=your-compatible-model-identifier
```

Obtain a key from [Google AI Studio](https://aistudio.google.com/apikey) and choose a model available to that key. The backend uses Google's [OpenAI-compatible chat completions interface](https://ai.google.dev/gemini-api/docs/openai) at `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`. Both the key and an explicit model identifier are required. No additional model software or Python SDK is needed.

When Gemini is selected, messages, the last eight conversation messages, preferences, provider-returned place summaries, and planning warnings are sent to Google for inference. The key stays in the backend and is not returned by the capabilities API, stored in trip records, or placed in frontend environment variables. Google quota/billing and model access apply. Errors such as missing credentials, rejected keys, rate limits, unavailable models, and malformed output appear in the assistant. There is no automatic provider fallback.

### Local model

Configure an already running server with an already loaded model that supports `/v1/chat/completions`:

```dotenv
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://localhost:1234/v1
LOCAL_LLM_MODEL=your-existing-model-identifier
LOCAL_LLM_API_KEY=
```

Local mode accepts only loopback inference endpoints. The application never installs a model runtime, downloads weights, invokes model management, or falls back to a cloud model. Missing configuration and connection errors appear in conversation. Structured form planning remains usable with either provider unavailable.

The model extracts destination, dates, duration, interests, traveler/room counts, transport, diet, and pace. Pydantic validates extracted values. Monetary fields and provider facts cannot be written through model output. Unsupported place references and malformed responses are rejected without saving changes. Explanations are model-generated text; scheduling and validation run independently.

## Data providers

| Capability | Provider | Setting and limitations |
| --- | --- | --- |
| City lookup | Open-Meteo geocoding | Keyless |
| Places, restaurants, lodging, emergency facilities | OpenStreetMap / Overpass | `OVERPASS_URL`; public servers may be busy or unavailable |
| Weather | Open-Meteo | Up to 16 days; partial coverage is labeled |
| Hotel offers | Amadeus production Hotel List/Search | `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET` |
| Walking/driving routes and driving traffic | TomTom | `TOMTOM_API_KEY` |
| Currency conversion | Explicit traveler-configured rate | Optional `INR_PER_USD`; no default |

Results carry source, availability, retrieval time, and cache expiry. Cached results retain their timestamp; the interface labels expired data stale. Requests have bounded timeouts/retries, expiring caches, and host-wide rate-limit backoff. Routing also has per-plan request/time limits. Missing/failed routing falls back to a clearly labeled geographic estimate, never fabricated traffic.

Discovery searches within 6 km of the resolved city center, capped at 400 OSM elements. Coverage is not exhaustive. Attractions use the original TF-IDF/cosine utility. Ratings and ticket prices are not fabricated. Place websites and map links allow source checks.

Hotel quotes cover `max(1, days - 1)` nights and the requested room count. They are full-stay snapshots, not reservations. Quotes in another currency do not enter totals without a usable explicit conversion. Lodging listings can be shown without hotel credentials, but prices and room availability remain unknown.

Opening-hours support is conservative: daily/weekly ranges, multiple daily intervals, and closed days. Unsupported expressions, including public-holiday rules, stay unknown. Opening hours never establish ticket inventory. Dietary tags describe listed options rather than a guarantee. Emergency contacts appear only when supplied by the source; the app cannot call or dispatch assistance.

Attribution: [OpenStreetMap contributors / ODbL](https://www.openstreetmap.org/copyright), [Open-Meteo](https://open-meteo.com/). Optional providers are identified alongside results.

## Money and expenses

Allowances are **total-trip amounts for all travelers**, in the selected currency. Blank means unknown; zero means the traveler explicitly expects no cost. Accommodation uses the cheapest usable live hotel quote, otherwise its allowance. Other categories use allowances.

Projected cost per category is `max(planned amount, recorded spending)`: spending replaces the covered part of an allowance instead of being counted twice. Actual spending in an unknown category contributes to a known lower bound, but the full total stays incomplete. An incomplete budget is never declared within budget. A lower bound above the budget is flagged. Currency changes are blocked after expenses exist.

The planner does not silently lower allowances to make an over-budget plan look feasible. It reports that conflict for the traveler to resolve.

## Monitoring and persistence

Checks run every 15 minutes (`MONITOR_INTERVAL_SECONDS`) for ongoing trips and trips starting within 15 days, while the backend runs. Startup resumes due checks from SQLite. The visible browser retrieves the saved version every 30 seconds. Weather, opening information, route times, hotel offers, expenses, and preferences trigger reevaluation.

Only validated schedules replace an itinerary. Locked, completed, committed, and already-started activities keep their dates and times. If constraints cannot be resolved within `MAX_REPLAN_ATTEMPTS` (default 3), the previous itinerary remains visible with current conflicts and updated budget information. Marking a commitment is a scheduling control, not a booking.

SQLite stores preferences, expenses, conversations, plans, monitoring state, and before/after revisions. Transactional expected-version checks return HTTP 409 for stale writes. A newer user edit wins over stale monitor work. Database: `data/trips.sqlite3`, or `TRIP_DB_PATH`. Database files and credentials are gitignored. Use one backend worker.

## Interfaces

- `GET /health`, `GET /capabilities`
- `POST /trips`, `GET /trips`, `GET /trips/{id}`
- `PATCH /trips/{id}`: version plus complete preferences and/or monitoring
- `POST /trips/{id}/refresh`: version
- `PATCH /trips/{id}/activities/{activity_id}`: version and locked/completed/committed flags
- `POST /trips/{id}/expenses`: version and expense
- `POST /trips/{id}/chat`: version and message
- `POST /chat/draft`: message, optional preferences
- `GET /trips/{id}/revisions`
- `POST /trip`: compatibility entry with legacy top-level sections and a saved trip ID; unknown prices and ratings now return null

Interactive schema: http://127.0.0.1:8000/docs. Existing-trip writes require the latest version. The Next.js proxy preserves error statuses and keeps provider credentials server-side.

`BaseAgent` remains the specialist contract. `LiveOrchestrator` extends the original orchestrator, `AdaptiveItineraryAgent` extends its scheduler, and `LiveTripValidator` extends its independent validator. Legacy algorithms remain available for explicitly injected inputs and regression tests; they do not load samples by default. The service layer owns storage and revisions. Python contracts have corresponding TypeScript types.

The LLM is a conversational interface, not a source of travel facts. This implementation does not claim a trained reinforcement-learning policy or a reproduced research-paper evaluation.

## Testing

Follow the root README commands. Tests use provider fixtures and temporary databases. The explicit `tests/browser_server.py` harness runs on port 8001 and is never imported by the normal application. Its weather-change endpoint exists only in that test harness. Live hotel, traffic, and model checks require their configured services; mocked tests are not live results. See VERIFICATION.md.

CLI example: `.\.venv\Scripts\python.exe app.py --destination Jaipur --days 3 --start-date 2026-10-02`. It uses real providers and the same local database.
