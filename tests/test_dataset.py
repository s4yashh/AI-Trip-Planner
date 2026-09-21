"""Dataset integrity: the CSV exists, parses, and exposes the expected schema."""

from __future__ import annotations

import csv

from utils.data_loader import EXPECTED_COLUMNS, load_poi_csv


def test_dataset_file_exists(dataset_path):
    assert dataset_path.is_file()


def test_dataset_loads_to_pois(loaded_pois):
    assert len(loaded_pois) > 0


def test_required_columns_present_in_header(dataset_path, expected_columns):
    with dataset_path.open(newline="", encoding="utf-8") as handle:
        header = next(csv.reader(handle))
    assert set(expected_columns) <= set(header)


def test_expected_columns_match_loader_contract():
    assert EXPECTED_COLUMNS == sorted(EXPECTED_COLUMNS, key=EXPECTED_COLUMNS.index)


def test_no_poi_duplicates(loaded_pois):
    ids = [poi.poi_id for poi in loaded_pois]
    assert len(ids) == len(set(ids))


def test_multiple_destinations_represented(loaded_pois):
    destinations = {poi.destination for poi in loaded_pois}
    assert len(destinations) >= 5


def test_multiple_categories_represented(loaded_pois):
    categories = {poi.category for poi in loaded_pois}
    assert len(categories) >= 5


def test_dataset_reloads_idempotently(dataset_path):
    assert len(load_poi_csv(dataset_path)) == len(load_poi_csv(dataset_path))