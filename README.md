# AI Trip Planner Based on Multi-Agent Artificial Intelligence

A prototype Python **AI Trip Planner** built on a multi-agent architecture.
One user request flows through three specialised agents coordinated by an
orchestrator to produce a complete personalised travel plan.

## Current implementation stage

**Stage 3 of 50% prototype — multi-agent workflow.**

Completed:
- **Stage 1 — foundation**: Pydantic models, CSV data loader with validation,
  cleaning utilities, abstract `BaseAgent` contract.
- **Stage 2 — specialised agents**: content-based `POIRecommendationAgent`
  (TF-IDF + cosine similarity + weighted ranking) and deterministic
  `ItineraryAgent` (day-wise chronological scheduling).
- **Stage 3 — coordination**: transparent `BudgetAgent` (cost estimation and
  budget comparison with saving tips) and `OrchestratorAgent` that wires all
  three agents end-to-end with real, non-faked execution status.

**Explicitly not yet implemented** (future stages): LLM integration, weather,
hotel, transportation, restaurant, traffic, emergency data, real-time APIs,
and the Streamlit UI. No code in this repository claims otherwise.

## Project structure

```text
ai-trip-planner/
├── app.py                     # CLI: dataset summary + full trip planning
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
├── services/                  # reserved for future agent orchestration layers
├── utils/
│   ├── __init__.py
│   ├── data_loader.py         # CSV loading, validation, coercion
│   ├── preprocessing.py       # cleaning helpers
│   └── text_features.py       # dependency-free TF-IDF + cosine similarity
├── tests/                     # pytest suite (unit + integration)
├── requirements.txt
└── README.md
```

## Dataset schema

`data/poi_dataset.csv` is **prototype/sample data** used to exercise the
recommendation logic. It is not sourced from a real, published tourism
dataset. It contains 40 records across 8 destinations (Paris, Tokyo,
New York, Rome, Bali, Dubai, London, Singapore) and 8 categories
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
- Dependencies are kept minimal on purpose:
  - `pydantic>=2.5` — data models
  - `pytest>=8.0` — testing
- No LangChain, LangGraph, CrewAI, AutoGen, or external APIs at this stage.

## Installation

```bash
cd ai-trip-planner
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the app

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

The `--plan` output includes the ranked POIs with explanations, a
day-wise itinerary with start/end times, a transparent budget breakdown,
cost-saving tips, and the real agent execution status.

## Running the tests

```bash
python -m pytest                  # or: pytest
python -m pytest -v               # verbose
```

The suite covers the data layer, the models, and all four agents
including an end-to-end integration test that pushes one user request
through the real POI, itinerary and budget agents via the orchestrator.