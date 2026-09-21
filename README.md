# AI Trip Planner Based on Multi-Agent Artificial Intelligence

A prototype Python foundation for a personalised tourism **AI Trip Planner**
that will later coordinate multiple specialised AI agents
(recommendation, itinerary, budget, ...).

## Current implementation stage

**Stage 1 of 50% prototype — project foundation only.**

Everything in this repository is limited to the scaffolding of a clean,
extensible codebase:

- POI data model and trip-request model (Pydantic)
- CSV data loader with column validation, type conversion and error handling
- Basic data-cleaning utilities
- Abstract `BaseAgent` contract
- Dataset, model and data-layer tests

**Explicitly not yet implemented** (future stages): recommendation agent,
itinerary agent, budget agent, LLM integration, real-time APIs, and the
Streamlit UI. No code in this repository claims otherwise.

## Project structure

```text
ai-trip-planner/
├── app.py                     # stage-1 CLI entry point (dataset loading + summary)
├── conftest.py                # shared pytest fixtures
├── data/
│   └── poi_dataset.csv        # prototype POI dataset (sample / not production data)
├── agents/
│   ├── __init__.py
│   └── base_agent.py          # abstract BaseAgent contract
├── models/
│   ├── __init__.py
│   └── schemas.py             # POI and UserTripRequest (Pydantic v2)
├── services/                  # reserved for future agent orchestration
├── utils/
│   ├── __init__.py
│   ├── data_loader.py         # CSV loading, validation, coercion
│   └── preprocessing.py       # cleaning helpers
├── tests/                     # pytest suite
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

## Running the app (stage 1)

Loads the dataset and prints a summary:

```bash
python app.py
python app.py --data path/to/other.csv
```

## Running the tests

```bash
python -m pytest                  # or: pytest
python -m pytest -v               # verbose
```