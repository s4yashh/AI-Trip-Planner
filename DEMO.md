# Faculty Demo Runbook — AI Trip Planner

Goal: show that the multi-agent pipeline is real, explain the architecture, and
back every claim with a live run. ~10 minutes.

Suggested flow: 1) CLI (no UI) → 2) same request through the web UI → 3) error
handling → 4) code walkthrough for questions.

---

## 0. Pre-flight (before faculty arrive)

```bash
cd ~/AIproject/ai-trip-planner
.venv/bin/python -m pytest -q          # expect: 86 passed
(cd frontend && npm test)              # expect: 22 passed
(cd frontend && npm run build)         # expect: clean build
```

Then start the servers (either `./run.sh` or two terminals).

---

## 1. CLI workflow — no browser (Stage 1–3)

Shows the backend works on its own and reveals exactly what each agent does.

```bash
.venv/bin/python app.py                           # dataset summary (48 POIs, 9 destinations)
.venv/bin/python app.py --plan \
  --destination Jaipur --days 2 --budget 600 \
  --interests "History, Architecture"
```

Point out in the output:
- **Recommendation agent**: ranked list with scores + a plain-language reason
  ("Strong match with selected interests: history, architecture").
- **Itinerary agent**: timed day schedule (max 4/day, durations respected) and
  a "Skipped (no slot fits)" line — proof it's not just listing POIs.
- **Budget agent**: transparent USD breakdown (accommodation/transport/food…),
  comparison vs. budget, and staying-within-budget advice.

---

## 2. Same request through the web (Stage 4)

Open http://localhost:3000/plan. Enter: Jaipur · 3 days · 30000 (INR) ·
History + Architecture + Culture → **Generate My Trip**.

Expected UI highlights:
- Gradient summary banner: destination, days, budget in ₹, estimated total.
- Ranked cards: match %, rating stars, duration, cost, recommendation reason.
- Day-by-day timeline with start/end times.
- Budget section: stacked bar chart of costs + "Over budget / shortfall" badge.
- **Agent Status panel**: live per-agent ✓/✗ — the honest execution report.

Key talking point: change the currency to USD or the interests to Food/Shopping
and regenerate — the plan, reasons, and budget genuinely change. Nothing is
hardcoded; the UI merely renders backend output.

---

## 3. Error handling — the system is honest

| Demo | What you should see |
| --- | --- |
| Destination `Atlantis` | "No matching places found" + Itinerary/Budget agents honestly show ✗ |
| Empty destination / 0 days / no interests | Red field-validation messages under the inputs |
| Stop backend (`pkill -f uvicorn`), then generate | Friendly "planning service could not be reached" banner — no stack trace, no crash |

---

## 4. For questions — where the implementation lives

- Multi-agent wiring: `agents/orchestrator_agent.py` (run(): recommend →
  weather → restaurants → schedule → budget → validate/re-plan, with real
  status capture; max 3 re-plan attempts).
- Recommendation math: `agents/poi_agent.py` + `utils/text_features.py` (TF-IDF + cosine similarity, no ML libs).
- Weather: `agents/weather_agent.py` + `services/weather_service.py` (real
  Open-Meteo forecasts, no key; `unavailable` state offline).
- Restaurants: `agents/restaurant_agent.py` + `services/places_service.py`
  (real Overpass listings ranked by our 0.40/0.25/0.20/0.15 formula;
  `data/restaurants.csv` fallback, labelled).
- Travel times: `services/routing_service.py` (real OSRM durations, labelled
  haversine fallback) feeding itinerary gaps.
- Validation engine: `validation/trip_validator.py` (13 checks, never mutates).
- Budget hard constraint: over-budget plans are pruned + re-validated; tiny
  budgets return exactly `No feasible itinerary found within the specified
  budget.` — try Jaipur / 3 days / ₹100 to show it.
- Scheduling: `agents/itinerary_agent.py` (exactly N days, no overlaps,
  travel-aware gaps, rainy-day indoor preference).
- Budget: `agents/budget_agent.py` (daily rates + dataset activity costs).
- API boundary & currency: `api/main.py`, `api/presenters.py` (INR/USD round-trip).
- Frontend proxy: `frontend/app/api/trip/route.ts` → so CORS never appears.
- Data: `data/poi_dataset.csv` (48 hand-authored sample POIs, 9 destinations).

## 5. What to say when asked "is this real AI?"

No LLM is used. The "AI" is a **multi-agent system**: hand-built algorithms
(TF-IDF ranking, greedy scheduling, rule-based budgeting, own restaurant
ranking, constraint validation) organized as interchangeable agents with real,
non-faked execution status. External APIs supply *data only* (weather,
listings, routes) — every decision is our algorithm, and the UI badges
(`Live data` / `Local dataset` / `Estimated` / `Unavailable`) always say
where data came from. That is the point of the academic prototype — and
it's a deliberate design choice, not a limitation.

## 6. Explicitly out of scope (say so if asked)

LLM summaries, hotel/flight booking, payments, emergency services, mobile app,
RL/deep-learning recommenders, production auth, real-time traffic. These are
listed as "planned next" in the UI's About page. Never claim them as
implemented.