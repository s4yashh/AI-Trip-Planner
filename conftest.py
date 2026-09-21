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