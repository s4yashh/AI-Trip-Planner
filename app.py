#!/usr/bin/env python3
"""AI Trip Planner - prototype bootstrap.

Stage 1 loads and validates the POI dataset; `--plan` runs the full
multi-agent workflow (POI -> itinerary -> budget) through the orchestrator.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from utils.data_loader import DataLoadError, DEFAULT_POI_DATASET, load_poi_csv, poi_count
from utils.preprocessing import standardise_category

DEFAULT_DATASET = DEFAULT_POI_DATASET


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
    parser = argparse.ArgumentParser(description="AI Trip Planner - prototype")
    parser.add_argument(
        "--data",
        type=str,
        default=str(DEFAULT_DATASET),
        help="path to the POI dataset CSV",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="run the full multi-agent trip planning workflow",
    )
    parser.add_argument("--destination", type=str, default="Rome")
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--budget", type=float, default=None)
    parser.add_argument("--interests", type=str, default="")
    return parser


def plan(
    destination: str,
    days: int,
    budget: float | None,
    interests: str,
    data_path: Path,
) -> int:
    from agents.orchestrator_agent import OrchestratorAgent
    from models.schemas import UserTripRequest

    interest_list = [item.strip() for item in interests.split(",") if item.strip()]

    try:
        orchestrator = OrchestratorAgent(pois=load_poi_csv(data_path))
        request = UserTripRequest(
            destination=destination,
            number_of_days=days,
            budget=budget,
            interests=interest_list,
        )
    except Exception as exc:  # noqa: BLE001 - surfaced for CLI diagnostics
        print(f"[app] plan failed: {exc}")
        return 1

    trip = orchestrator.run(request)

    print("\n" + trip.trip_summary)
    print("\nRecommended POIs")
    for i, rec in enumerate(trip.recommended_pois, start=1):
        print(
            f"  {i:2d}. {rec.name:32s} score={rec.recommendation_score:.3f} "
            f"${rec.estimated_cost:7.2f} | {rec.reason}"
        )

    print("\nItinerary")
    if trip.itinerary.days:
        for day in trip.itinerary.days:
            print(f"  Day {day.day_number}")
            for item in day.items:
                print(
                    f"     {item.start_time} - {item.end_time}  {item.name}  "
                    f"({item.duration_hours}h, ${item.estimated_cost:.2f})"
                )
        if trip.itinerary.skipped_poi_ids:
            print(f"  Skipped (no slot fits): {', '.join(trip.itinerary.skipped_poi_ids)}")
    else:
        print("  No itinerary generated.")

    print("\nBudget Analysis")
    if trip.budget_analysis:
        budget = trip.budget_analysis
        print(f"  Estimated total  : ${budget.total_cost:,.2f}")
        print(f"  User budget      : ${budget.user_budget:,.2f}" if budget.user_budget is not None
              else "  User budget      : not set")
        print(f"  Within budget    : {budget.within_budget}")
        for item in budget.breakdown:
            print(f"     {item.category:16s} ${item.amount:8.2f}  ({item.basis})")
        for suggestion in budget.suggestions:
            print(f"  Tip: {suggestion}")
    else:
        print("  No budget analysis generated.")

    print("\nAgent Execution Status")
    for line in trip.agent_execution_status.to_text():
        print(f"  {line}")
    for error in trip.errors:
        print(f"  Error: {error}")
    return 0


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.plan:
        return plan(args.destination, args.days, args.budget, args.interests, Path(args.data))
    pois = load_dataset(args.data)
    if not pois:
        return 1
    summary(pois)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())