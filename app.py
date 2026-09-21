#!/usr/bin/env python3
"""AI Trip Planner - prototype bootstrap.

Stage 1 only: loads and validates the POI dataset. No agents or
recommendation logic are executed here; that is future work.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from utils.data_loader import DataLoadError, load_poi_csv, poi_count
from utils.preprocessing import standardise_category

DEFAULT_DATASET = Path(__file__).resolve().parent / "data" / "poi_dataset.csv"


def load_dataset(path: str | Path) -> list:
    """Load the dataset, returning an empty list on failure."""
    from models.schemas import POI  # noqa: PLC0415

    try:
        return load_poi_csv(path)
    except DataLoadError as exc:
        print(f"[app] error: {exc}")
        return []


def summary(pois: list[POI]) -> None:
    """Print a compact summary of the loaded dataset."""
    destinations = sorted({poi.destination for poi in pois})
    categories = sorted({standardise_category(poi.category) for poi in pois})
    cost_total = sum(poi.estimated_cost for poi in pois)

    print(f"\nDataset summary")
    print(f"  POIs loaded    : {poi_count(pois)}")
    print(f"  Destinations   : {len(destinations)} -> {', '.join(destinations)}")
    print(f"  Categories     : {len(categories)} -> {', '.join(categories)}")
    print(f"  Est. total cost: ${cost_total:,.2f} across all POIs")
    print(f"  Top rated      : {max(pois, key=lambda p: p.rating).name}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Trip Planner - stage 1 prototype")
    parser.add_argument(
        "--data",
        type=str,
        default=str(DEFAULT_DATASET),
        help="path to the POI dataset CSV",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    pois = load_dataset(args.data)
    if not pois:
        return 1
    summary(pois)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())