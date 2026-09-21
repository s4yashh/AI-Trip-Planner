"""Shared pytest configuration and fixtures for the project."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "data" / "poi_dataset.csv"

EXPECTED_COLUMNS = [
    "poi_id",
    "name",
    "destination",
    "category",
    "description",
    "rating",
    "review_count",
    "visit_duration_hours",
    "estimated_cost",
    "latitude",
    "longitude",
]


@pytest.fixture(scope="session")
def dataset_path() -> Path:
    return DATASET


@pytest.fixture(scope="session")
def loaded_pois(dataset_path):
    from utils.data_loader import load_poi_csv

    return load_poi_csv(dataset_path)


@pytest.fixture(scope="session")
def expected_columns() -> list[str]:
    return EXPECTED_COLUMNS


@pytest.fixture
def make_poi():
    from models.schemas import POI

    def factory(**overrides):
        base = {
            "poi_id": "POI-X",
            "name": "Place",
            "destination": "Test City",
            "category": "Museum",
            "description": "A sampled point of interest.",
            "rating": 4.0,
            "review_count": 100,
            "visit_duration_hours": 2.0,
            "estimated_cost": 10.0,
            "latitude": 0.0,
            "longitude": 0.0,
        }
        base.update(overrides)
        return POI(**base)

    return factory


@pytest.fixture
def make_rec():
    from models.schemas import POIRecommendation

    def factory(**overrides):
        base = {
            "poi_id": "POI-1",
            "name": "Place",
            "category": "museum",
            "recommendation_score": 0.5,
            "rating": 4.0,
            "visit_duration_hours": 2.0,
            "estimated_cost": 10.0,
            "reason": "General attraction in Test City",
        }
        base.update(overrides)
        return POIRecommendation(**base)

    return factory