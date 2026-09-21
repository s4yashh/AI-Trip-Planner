"""Data loader behaviour: typing, validation and error reporting."""

from __future__ import annotations

import csv
import io

import pytest

from utils.data_loader import DataLoadError, load_poi_csv
from utils.preprocessing import standardise_category


def test_loader_returns_typed_pois(loaded_pois):
    poi = loaded_pois[0]
    assert isinstance(poi.rating, float)
    assert isinstance(poi.review_count, int)
    assert isinstance(poi.estimated_cost, float)


def test_loader_missing_file_raises(tmp_path):
    with pytest.raises(DataLoadError, match="not found"):
        load_poi_csv(tmp_path / "missing.csv")


def test_loader_invalid_columns_raise(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("poi_id,name\n1,A\n", encoding="utf-8")
    with pytest.raises(DataLoadError, match="column mismatch"):
        load_poi_csv(bad)


def test_loader_missing_required_column_raise(tmp_path):
    bad = tmp_path / "missing_rating.csv"
    header = ["poi_id", "name", "destination", "category", "description",
              "review_count", "visit_duration_hours", "estimated_cost",
              "latitude", "longitude"]
    buffer = io.StringIO()
    csv.writer(buffer).writerow(header)
    bad.write_text(buffer.getvalue(), encoding="utf-8")
    with pytest.raises(DataLoadError, match="column mismatch"):
        load_poi_csv(bad)


def test_loader_non_numeric_rating_raises(tmp_path):
    bad = tmp_path / "nonnumeric.csv"
    bad.write_text(
        "poi_id,name,destination,category,description,rating,review_count,"
        "visit_duration_hours,estimated_cost,latitude,longitude\n"
        "POI001,Test,City,Landmark,Desc.,not-a-number,10,1.0,0.0,0.0,0.0\n",
        encoding="utf-8",
    )
    with pytest.raises(DataLoadError, match="'rating' expected a float"):
        load_poi_csv(bad)


def test_loader_non_integer_review_count_raises(tmp_path):
    bad = tmp_path / "noninteger.csv"
    bad.write_text(
        "poi_id,name,destination,category,description,rating,review_count,"
        "visit_duration_hours,estimated_cost,latitude,longitude\n"
        "POI001,Test,City,Landmark,Desc.,4.5,tens,1.0,0.0,0.0,0.0\n",
        encoding="utf-8",
    )
    with pytest.raises(DataLoadError, match="'review_count' expected an integer"):
        load_poi_csv(bad)


def test_loader_empty_dataset_raises(tmp_path):
    bad = tmp_path / "empty.csv"
    bad.write_text(
        "poi_id,name,destination,category,description,rating,review_count,"
        "visit_duration_hours,estimated_cost,latitude,longitude\n",
        encoding="utf-8",
    )
    with pytest.raises(DataLoadError, match="no valid POI rows"):
        load_poi_csv(bad)


def test_standardise_category():
    assert standardise_category("  Food  ") == "food"