"""API integration tests: HTTP boundary -> orchestrator -> real agents."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_trip_jaipur_full_flow():
    payload = {
        "destination": "Jaipur",
        "number_of_days": 3,
        "budget": 30000,
        "interests": ["History", "Architecture", "Culture"],
        "currency": "INR",
    }
    response = client.post("/trip", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["trip_summary"]["destination"] == "Jaipur"
    assert data["trip_summary"]["number_of_days"] == 3
    assert data["recommended_pois"]
    assert data["itinerary"]["days"]
    assert data["budget_analysis"] is not None
    assert data["agent_execution_status"]["poi_recommendation"] is True
    assert data["agent_execution_status"]["itinerary"] is True
    assert data["agent_execution_status"]["budget"] is True
    assert data["errors"] == []

    first = data["recommended_pois"][0]
    for field in ("poi_id", "name", "category", "recommendation_score",
                  "rating", "visit_duration_hours", "estimated_cost", "reason"):
        assert field in first

    budget = data["budget_analysis"]
    assert budget["total_cost"] > 0
    assert sum(
        budget[category] for category in
        ("accommodation", "transportation", "food", "activities", "miscellaneous")
    ) == budget["total_cost"]


def test_trip_inr_budget_round_trips_through_conversion():
    payload = {
        "destination": "Jaipur",
        "number_of_days": 2,
        "budget": 30000,
        "interests": ["History", "Architecture"],
        "currency": "INR",
    }
    response = client.post("/trip", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["trip_summary"]["budget"] == 30000
    assert data["budget_analysis"]["user_budget"] == 30000
    assert data["budget_analysis"]["within_budget"] in {True, False}
    assert data["budget_analysis"]["total_cost"] > 0

    usd_budget = 30000 / 83.0
    usd_response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 2,
            "budget": usd_budget,
            "interests": ["History", "Architecture"],
            "currency": "USD",
        },
    )
    assert usd_response.status_code == 200
    usd_data = usd_response.json()

    assert usd_data["budget_analysis"]["user_budget"] == round(usd_budget, 2)
    assert (
        usd_data["budget_analysis"]["within_budget"]
        == data["budget_analysis"]["within_budget"]
    )


def test_trip_paris_different_preferences():
    response = client.post(
        "/trip",
        json={
            "destination": "Paris",
            "number_of_days": 2,
            "budget": 500,
            "interests": ["Food"],
            "currency": "USD",
        },
    )
    assert response.status_code == 200
    data = response.json()
    names = {rec["name"] for rec in data["recommended_pois"]}
    assert "Le Marais Walking Tour" in names
    assert all(
        rec["category"] in {"museum", "food", "landmark", "entertainment", "adventure"}
        for rec in data["recommended_pois"]
    )


def test_trip_extremely_low_budget_returns_no_feasible_itinerary():
    response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 3,
            "budget": 100,
            "interests": ["History"],
            "currency": "INR",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trip_summary"]["message"] == (
        "No feasible itinerary found within the specified budget."
    )
    assert "No feasible itinerary found within the specified budget." in data["errors"]
    assert data["recommended_pois"] == []
    assert data["itinerary"]["days"] == []
    assert data["budget_analysis"] is None


def test_trip_no_matching_destination_is_graceful():
    response = client.post(
        "/trip",
        json={"destination": "Atlantis", "number_of_days": 2, "interests": ["Food"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_pois"] == []
    assert data["itinerary"]["days"] == []
    assert data["budget_analysis"] is None
    assert data["errors"]
    assert data["agent_execution_status"]["poi_recommendation"] is True
    assert data["agent_execution_status"]["itinerary"] is False


def test_trip_missing_destination_is_rejected():
    response = client.post("/trip", json={"number_of_days": 2, "interests": ["Food"]})
    assert response.status_code == 422


def test_trip_invalid_days_is_rejected():
    response = client.post(
        "/trip", json={"destination": "Rome", "number_of_days": 0, "interests": ["Food"]}
    )
    assert response.status_code == 422


def test_trip_negative_budget_is_rejected():
    response = client.post(
        "/trip",
        json={"destination": "Rome", "number_of_days": 2, "budget": -5, "interests": []},
    )
    assert response.status_code == 422


def test_trip_invalid_currency_is_rejected():
    response = client.post(
        "/trip",
        json={"destination": "Rome", "number_of_days": 2, "currency": "EUR"},
    )
    assert response.status_code == 422


def _minutes(text: str) -> int:
    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)


def test_trip_budget_20000_inr_never_exceeded():
    response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 3,
            "budget": 20000,
            "interests": ["History", "Architecture"],
            "currency": "INR",
        },
    )
    assert response.status_code == 200
    data = response.json()
    budget = data["budget_analysis"]
    assert budget is not None
    assert budget["total_cost"] <= 20000
    assert budget["within_budget"] is True
    assert data["trip_summary"]["total_estimated_cost"] <= 20000
    assert data["errors"] == []


def test_trip_budget_30000_inr_never_exceeded():
    response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 3,
            "budget": 30000,
            "interests": ["History", "Architecture", "Culture"],
            "currency": "INR",
        },
    )
    assert response.status_code == 200
    data = response.json()
    budget = data["budget_analysis"]
    assert budget is not None
    assert budget["total_cost"] <= 30000
    assert budget["within_budget"] is True


def test_trip_three_days_produce_exactly_three_days():
    response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 3,
            "budget": 30000,
            "interests": ["History"],
            "currency": "INR",
        },
    )
    assert response.status_code == 200
    days = response.json()["itinerary"]["days"]
    assert [day["day_number"] for day in days] == [1, 2, 3]


def test_trip_itinerary_has_no_overlapping_times():
    response = client.post(
        "/trip",
        json={
            "destination": "Rome",
            "number_of_days": 3,
            "budget": 700,
            "interests": ["Museum", "Food"],
            "currency": "USD",
        },
    )
    assert response.status_code == 200
    for day in response.json()["itinerary"]["days"]:
        previous_end = None
        for item in day["items"]:
            start, end = _minutes(item["start_time"]), _minutes(item["end_time"])
            assert end - start == round(item["duration_hours"] * 60)
            if previous_end is not None:
                assert start >= previous_end
            previous_end = end


def test_trip_budget_components_sum_exactly_to_total():
    response = client.post(
        "/trip",
        json={
            "destination": "Paris",
            "number_of_days": 2,
            "budget": 500,
            "interests": ["Food"],
            "currency": "USD",
        },
    )
    assert response.status_code == 200
    budget = response.json()["budget_analysis"]
    assert budget["total_cost"] == (
        budget["accommodation"]
        + budget["transportation"]
        + budget["food"]
        + budget["activities"]
        + budget["miscellaneous"]
    )


def test_trip_interests_change_poi_ranking():
    food = client.post(
        "/trip",
        json={
            "destination": "Paris",
            "number_of_days": 2,
            "interests": ["Food"],
            "currency": "USD",
        },
    )
    museum = client.post(
        "/trip",
        json={
            "destination": "Paris",
            "number_of_days": 2,
            "interests": ["Museum"],
            "currency": "USD",
        },
    )
    assert food.status_code == 200
    assert museum.status_code == 200
    food_order = [rec["poi_id"] for rec in food.json()["recommended_pois"]]
    museum_order = [rec["poi_id"] for rec in museum.json()["recommended_pois"]]
    assert food_order != museum_order


def test_trip_destination_returns_only_its_pois():
    from utils.data_loader import load_poi_csv
    from pathlib import Path

    dataset = Path(__file__).resolve().parent / "fixtures" / "poi_dataset.csv"
    allowed = {
        poi.poi_id for poi in load_poi_csv(dataset) if poi.destination == "Rome"
    }
    response = client.post(
        "/trip",
        json={
            "destination": "Rome",
            "number_of_days": 2,
            "interests": ["History"],
            "currency": "USD",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_pois"]
    assert {rec["poi_id"] for rec in data["recommended_pois"]} <= allowed
    planned = [
        item["poi_id"] for day in data["itinerary"]["days"] for item in day["items"]
    ]
    assert set(planned) <= allowed
    assert len(planned) == len(set(planned))


def test_trip_agent_status_tracks_new_agents():
    response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 2,
            "budget": 30000,
            "interests": ["History"],
            "currency": "INR",
        },
    )
    assert response.status_code == 200
    status = response.json()["agent_execution_status"]
    for key in (
        "orchestrator",
        "poi_recommendation",
        "weather",
        "restaurant",
        "itinerary",
        "budget",
        "validator",
    ):
        assert key in status
    assert status["poi_recommendation"] is True
    assert status["itinerary"] is True
    assert status["budget"] is True
    assert status["validator"] is True


def test_trip_includes_weather_and_restaurant_sections():
    response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 2,
            "budget": 30000,
            "interests": ["Food"],
            "currency": "INR",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "weather_report" in data
    assert "restaurant_list" in data
    assert "validation_report" in data
    assert data["weather_report"]["source"] in {"live", "unavailable", "dataset"}
    assert data["restaurant_list"]["source"] in {"live", "unavailable", "dataset"}


def test_trip_start_date_is_accepted():
    response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 2,
            "budget": 30000,
            "interests": ["History"],
            "currency": "INR",
            "start_date": "2026-10-01",
        },
    )
    assert response.status_code == 200


def test_trip_invalid_start_date_is_rejected():
    response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 2,
            "interests": ["History"],
            "start_date": "not-a-date",
        },
    )
    assert response.status_code == 422

# Legacy contract tests explicitly inject algorithm fixtures, never runtime defaults.
import pytest
@pytest.fixture(autouse=True)
def legacy_algorithm_inputs(monkeypatch, loaded_pois):
    import api.main as api
    from agents.orchestrator_agent import OrchestratorAgent
    monkeypatch.setattr(api, "_orchestrator", OrchestratorAgent(pois=loaded_pois))
