# AI Trip Planner Based on Multi-Agent Artificial Intelligence

A prototype **AI Trip Planner** built on a multi-agent architecture. One user
request flows through three specialised agents coordinated by an orchestrator
to produce a complete personalised travel plan — served to a responsive web
frontend through a small FastAPI boundary.

## Current implementation stage

**50% prototype — multi-agent backend + web interface.**

Completed:
- **Stage 1 — foundation**: Pydantic models, CSV data loader with validation,
  cleaning utilities, abstract `BaseAgent` contract.
- **Stage 2 — specialised agents**: content-based `POIRecommendationAgent`
  (TF-IDF + cosine similarity + weighted ranking) and deterministic
  `ItineraryAgent` (day-wise chronological scheduling).
- **Stage 3 — coordination**: transparent `BudgetAgent` (cost estimation and
  budget comparison with saving tips) and `OrchestratorAgent` that wires all
  three agents end-to-end with real, non-faked execution status.
- **Stage 4 — interface**: FastAPI HTTP boundary (`POST /trip`) and a
  Vercel-ready Next.js (App Router, TypeScript, Tailwind) frontend with a
  trip form, live results, and an honest per-agent status panel.

All agent results you see in the UI are computed live by the backend — nothing
is staged or hardcoded in the frontend.

**Explicitly not yet implemented** (future stages): LLM integration, weather,
hotel, transportation, restaurant, traffic, emergency data, real-time currency
APIs, and user accounts. No code in this repository claims otherwise.

## Project structure

```text
ai-trip-planner/
├── app.py                     # CLI: dataset summary + full trip planning
├── api/
│   ├── main.py                # FastAPI app (GET /health, POST /trip)
│   └── presenters.py          # JSON contract + currency conversion
├── conftest.py                # shared pytest fixtures
├── data/
│   └── poi_dataset.csv        # prototype POI dataset (sample / not production data)
├── agents/
│   ├── __init__.py            # exports all implemented agents
│   ├── base_agent.py          # abstract BaseAgent contract
│   ├── poi_agent.py           # content-based POI recommendation
│   ├── itinerary_agent.py     # deterministic day-wise scheduling
│   ├── budget_agent.py        # transparent trip cost estimation
│   └── orchestrator_agent.py  # coordinates the three specialised agents
├── models/
│   ├── __init__.py
│   └── schemas.py             # POI, UserTripRequest, recommendation,
│                              # itinerary, budget and trip-plan models
├── frontend/                  # Next.js App Router + TS + Tailwind web app
│   ├── app/                   # pages (/, /plan, /about) + /api/trip proxy
│   ├── components/            # form, result cards, agent status, loading
│   ├── lib/                   # API client, validation, currency formatting
│   ├── types/trip.ts          # shared types mirroring the API contract
│   └── tests/                 # Vitest unit tests
├── services/                  # reserved for future agent orchestration layers
├── utils/
│   ├── __init__.py
│   ├── data_loader.py         # CSV loading, validation, coercion
│   ├── preprocessing.py       # cleaning helpers
│   └── text_features.py       # dependency-free TF-IDF + cosine similarity
├── tests/                     # pytest suite (unit + integration, incl. API)
├── requirements.txt
└── README.md
```

## Dataset schema

`data/poi_dataset.csv` is **prototype/sample data** used to exercise the
recommendation logic. It is not sourced from a real, published tourism
dataset. It contains 48 records across 9 destinations (Paris, Tokyo,
New York, Rome, Bali, Dubai, London, Singapore, Jaipur) and 8 categories
(Landmark, Museum, Food, Culture, Adventure, Entertainment, Outdoors,
Shopping).

Columns:

| Column                 | Type     | Description                             |
| ---------------------- | -------- | --------------------------------------- |
| `poi_id`               | str      | Unique identifier                       |
| `name`                 | str      | Point-of-interest name                  |
| `destination`          | str      | City / region                           |
| `category`             | str      | Tourism category                        |
| `description`          | str      | Short description                       |
| `rating`               | float    | 0.0 – 5.0                               |
| `review_count`         | int      | Number of reviews                       |
| `visit_duration_hours` | float    | Typical visit length                    |
| `estimated_cost`       | float    | Estimated entry / activity cost (USD)   |
| `latitude`             | float    | Geographic latitude                     |
| `longitude`            | float    | Geographic longitude                    |

## Requirements

- Python 3.11+ (developed and tested on 3.14)
- Node.js 20+ (frontend uses Next.js 16)
- Backend dependencies (kept minimal on purpose):
  - `pydantic>=2.5` — data models
  - `fastapi>=0.110` + `uvicorn>=0.29` — HTTP API
  - `httpx>=0.27` — API test client
  - `pytest>=8.0` — testing
- No LangChain, LangGraph, CrewAI, AutoGen, or external AI APIs at this stage.

## Installation

```bash
cd ai-trip-planner
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Frontend dependencies:

```bash
cd frontend
npm install
```

## Running the app

### CLI

Loads the dataset and prints a summary:

```bash
python app.py
python app.py --data path/to/other.csv
```

Runs the full multi-agent workflow (POI recommendation -> itinerary ->
budget) through the orchestrator:

```bash
python app.py --plan --destination Tokyo --days 3 --budget 600 --interests "Food, Culture"
```

The `--plan` output includes the ranked POIs with explanations, a day-wise
itinerary with start/end times, a transparent budget breakdown, cost-saving
tips, and the real agent execution status.

### Web app

```bash
# Terminal 1 — Python backend (FastAPI)
uvicorn api.main:app --reload        # serves http://localhost:8000

# Terminal 2 — Next.js frontend
cd frontend
npm run dev                          # serves http://localhost:3000
```

Open http://localhost:3000/plan and try e.g. Jaipur, 3 days, ₹30,000, with
History / Architecture / Culture interests.

How the pieces talk: the browser calls `POST /api/trip` on Next.js, which
proxies to the FastAPI backend (`AI_BACKEND_URL`, default
`http://localhost:8000`). FastAPI runs the orchestrator and returns the plan
as JSON. Set `NEXT_PUBLIC_API_URL` to bypass the same-origin proxy if needed.

Currency: the internal agents work in USD; the API converts inputs and outputs
to the requested currency using a **fixed prototype rate** (`INR_PER_USD`,
default 83.0). This is not a live exchange rate.

## Running the tests

Backend (unit + integration, including the HTTP API):

```bash
python -m pytest                  # or: pytest
python -m pytest -v               # verbose
```

Frontend (Vitest): form validation, currency formatting, API client with a
mocked `fetch`.

```bash
cd frontend
npm test
npm run build                     # production build must also pass
```

The pytest suite covers the data layer, the models, all four agents, and end-to-end
HTTP tests that push user requests through the real agents via the orchestrator.