"""Live-data CLI. Shares persistence and agents with the web application."""
import argparse
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
from models.live import Preferences
from services.trip_service import TripService


def main():
    parser = argparse.ArgumentParser(description="Create a live trip and save it locally")
    parser.add_argument("--destination", required=True)
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--start-date")
    parser.add_argument("--budget", type=float)
    parser.add_argument("--currency", choices=["INR", "USD"], default="INR")
    parser.add_argument("--interests", default="")
    args = parser.parse_args()
    values = dict(destination=args.destination, number_of_days=args.days, budget=args.budget,
                  currency=args.currency, interests=[x.strip() for x in args.interests.split(",") if x.strip()])
    if args.start_date:
        values["start_date"] = args.start_date
    trip = TripService().create(Preferences(**values))
    print(trip.model_dump_json(indent=2))
    return 0 if trip.plan.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
