"""Load the raw POI dataset from CSV with validation and type conversion."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from models.schemas import POI

DEFAULT_POI_DATASET = Path(__file__).resolve().parent.parent / "data" / "poi_dataset.csv"

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

MISSING_TOKENS = {"", "nan", "none", "null", "n/a", "na"}


class DataLoadError(Exception):
    """Raised when the POI dataset cannot be loaded or validated."""


def _is_missing(value: str) -> bool:
    return value.strip().lower() in MISSING_TOKENS


def _coerce(value: str, column: str) -> object:
    """Convert a raw CSV cell to its typed value, or None when missing."""
    if _is_missing(value):
        return None
    if column in {"rating", "visit_duration_hours", "estimated_cost", "latitude", "longitude"}:
        try:
            return float(value.strip())
        except ValueError as exc:
            raise DataLoadError(
                f"column '{column}' expected a float, got {value!r}"
            ) from exc
    if column == "review_count":
        try:
            return int(value.strip())
        except ValueError as exc:
            raise DataLoadError(
                f"column 'review_count' expected an integer, got {value!r}"
            ) from exc
    return value.strip()


def validate_columns(columns: list[str]) -> None:
    """Ensure the CSV header matches the expected schema."""
    missing = [col for col in EXPECTED_COLUMNS if col not in columns]
    if len(columns) != len(EXPECTED_COLUMNS) or set(columns) != set(EXPECTED_COLUMNS):
        raise DataLoadError(
            "column mismatch: expected "
            f"{EXPECTED_COLUMNS}, got {columns}. Missing: {missing}"
        )


def load_poi_csv(path: str | Path) -> list[POI]:
    """Load and validate the POI dataset, returning a list of :class:`POI`.

    Raises
    ------
    DataLoadError
        If the file is missing, the header is invalid, cells cannot be
        converted, or a row fails POI model validation.
    """
    csv_path = Path(path)
    if not csv_path.is_file():
        raise DataLoadError(f"dataset file not found: {csv_path}")

    created = 0
    rejected = 0
    pois: list[POI] = []

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        validate_columns(reader.fieldnames or [])

        for line, raw_row in enumerate(reader, start=2):
            coerced = {column: _coerce(raw_row.get(column, ""), column) for column in EXPECTED_COLUMNS}
            if coerced["poi_id"] in (None, ""):
                rejected += 1
                continue
            try:
                pois.append(POI(**coerced))
                created += 1
            except Exception as exc:  # noqa: BLE001 - surfaced as a load error
                rejected += 1
                raise DataLoadError(
                    f"row {line} failed POI validation: {exc}"
                ) from exc

    if created == 0:
        raise DataLoadError(f"no valid POI rows could be loaded from {csv_path}")
    if rejected > 0:
        print(
            f"[data_loader] loaded {created} POIs, skipped {rejected} "
            "row(s) with missing poi_id or invalid data"
        )
    return pois


def poi_count(pois: Iterable[POI]) -> int:
    """Number of POI records in a collection."""
    return sum(1 for _ in pois)