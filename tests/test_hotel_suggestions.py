"""Hotel suggestion contract tests; fixture providers and fake AI only."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.hotel_routes import get_hotel_service
from models.hotels import HotelSearch, HotelSuggestion
from models.live import Place, Source
from services.hotel_suggestion_service import HotelSuggestionService, LodgingFinder, assign_labels, osm_amenities
from services.live_providers import ProviderError
from services.local_llm import LocalModelError


SEARCH = HotelSearch(destination="Goa", check_in=date(2026, 11, 1), check_out=date(2026, 11, 4), adults=2, rooms=1)


def lodging(place_id, name, **tags):
    return Place(id=place_id, name=name, kind="lodging", latitude=15.5, longitude=73.8,
                 tags={"tourism": "hotel", **tags}, source=Source(provider="Fixture places", status="live"))


class Providers:
    def __init__(self, places=None, discover_error=None, geocode_error=None):
        self.places = places if places is not None else [
            lodging("osm-1", "Sea View Hotel", stars="4", internet_access="wlan", **{"addr:suburb": "Calangute"}),
            lodging("osm-2", "Budget Inn", **{"addr:street": "MG Road"}),
            lodging("osm-3", "Palm Resort", swimming_pool="yes"),
            lodging("osm-city", "goa"),  # a listing named after the city is noise
            Place(id="osm-museum", name="Museum", kind="museum", latitude=15.5, longitude=73.8,
                  source=Source(provider="Fixture places", status="live")),
        ]
        self.discover_error = discover_error
        self.geocode_error = geocode_error
        self.discover_calls = 0

    def geocode(self, destination):
        if self.geocode_error:
            raise self.geocode_error
        return {"name": "Goa", "admin1": "Goa", "country": "India", "latitude": 15.5, "longitude": 73.8}, Source(provider="Fixture geocoder", status="live")

    def discover(self, latitude, longitude):
        self.discover_calls += 1
        if self.discover_error:
            raise self.discover_error
        return self.places, Source(provider="Fixture places", status="live")


def ai_reply(rows):
    calls = []
    def enrich(system, user):
        calls.append((system, user))
        return {"hotels": rows}
    enrich.calls = calls
    return enrich


ESTIMATES = [
    {"id": "osm-1", "price_per_night": 6000, "rating": 4.6, "amenities": ["Pool", "Spa"]},
    {"id": "osm-2", "price_per_night": 1500, "rating": 3.6, "amenities": ["Wi-Fi"]},
    {"id": "osm-3", "price_per_night": 3000, "rating": 4.4, "amenities": ["Breakfast"]},
    {"id": "invented", "price_per_night": 1, "rating": 5},
]


def service(providers=None, enrich=None, ai=True):
    return HotelSuggestionService(providers or Providers(), enrich=enrich or ai_reply(ESTIMATES),
                                  ai_enabled=lambda: ai, ai_name=lambda: "Gemini")


def test_real_listings_enriched_with_labelled_ai_estimates():
    enrich = ai_reply(ESTIMATES)
    result = service(enrich=enrich).suggest(SEARCH)
    by_name = {s.name: s for s in result.suggestions}
    assert set(by_name) == {"Sea View Hotel", "Budget Inn", "Palm Resort"}  # museum and unknown ids excluded
    assert result.ai_used and result.approximate and result.nights == 3
    assert result.resolved_location == "Goa, India"
    assert by_name["Budget Inn"].labels == ["Cheapest"]
    assert by_name["Sea View Hotel"].labels == ["Best rated"]
    assert by_name["Palm Resort"].labels == ["Best value"]
    assert [s.name for s in result.suggestions][:3] == ["Budget Inn", "Sea View Hotel", "Palm Resort"]
    assert by_name["Sea View Hotel"].price_basis == "ai_estimate"
    assert by_name["Sea View Hotel"].rating_basis == "ai_estimate"
    # Map-provided amenities are kept rather than replaced by estimates.
    assert by_name["Sea View Hotel"].amenities == ["Wi-Fi"]
    assert by_name["Sea View Hotel"].amenities_basis == "openstreetmap"
    assert by_name["Sea View Hotel"].area == "Calangute"
    assert by_name["Palm Resort"].amenities == ["Pool"]
    assert result.sources["estimates"].status == "estimated"
    assert "Goa" in enrich.calls[0][1] and "3 nights" in enrich.calls[0][1]


def test_without_ai_shows_real_names_and_no_invented_prices():
    enrich = ai_reply(ESTIMATES)
    result = service(enrich=enrich, ai=False).suggest(SEARCH)
    assert not enrich.calls
    assert not result.ai_used
    assert all(s.price_per_night is None for s in result.suggestions)
    sea_view = next(s for s in result.suggestions if s.name == "Sea View Hotel")
    assert sea_view.rating == 4 and sea_view.rating_basis == "openstreetmap"
    assert sea_view.labels == ["Best rated"]
    assert all("Cheapest" not in s.labels for s in result.suggestions)
    assert "approximate prices" in result.message


def test_ai_failure_degrades_without_crashing():
    def broken(system, user):
        raise LocalModelError("Gemini returned HTTP 429.")
    result = service(enrich=broken).suggest(SEARCH)
    assert len(result.suggestions) == 3
    assert not result.ai_used
    assert "AI estimates unavailable" in result.message


def test_malformed_ai_values_are_ignored():
    rows = [{"id": "osm-1", "price_per_night": "cheap", "rating": 9, "amenities": "pool"},
            {"id": "osm-2", "price_per_night": float("inf"), "rating": True, "amenities": [""]}]
    result = service(enrich=ai_reply(rows)).suggest(SEARCH)
    assert all(s.price_per_night is None for s in result.suggestions)
    assert not result.ai_used
    assert "did not return usable estimates" in result.message


def test_map_outage_uses_unverified_ai_suggestions():
    rows = [{"name": "Taj Fort Aguada", "area": "Sinquerim", "price_per_night": 18000, "rating": 4.7, "amenities": ["Pool"]},
            {"name": "Taj Fort Aguada", "price_per_night": 1},  # duplicate dropped
            {"name": "Zostel Goa", "area": "Anjuna", "price_per_night": 900, "rating": 4.3}]
    providers = Providers(discover_error=ProviderError("Overpass unavailable", retryable=True))
    result = service(providers, enrich=ai_reply(rows)).suggest(SEARCH)
    assert [s.name for s in result.suggestions] == ["Zostel Goa", "Taj Fort Aguada"]
    assert all(not s.verified_listing for s in result.suggestions)
    assert "not been checked against map data" in result.message
    assert result.sources["lodging"].status == "unavailable"


def test_no_listings_and_no_ai_returns_empty_state():
    result = service(Providers(places=[]), ai=False).suggest(SEARCH)
    assert result.suggestions == []
    assert "No hotel listings found" in result.message


def test_results_are_cached_per_search():
    providers = Providers()
    hotels = service(providers)
    hotels.suggest(SEARCH)
    hotels.suggest(SEARCH)
    assert providers.discover_calls == 1


def test_labels_need_data_and_prefer_distinct_best_value():
    single = [HotelSuggestion(id="a", name="A", price_per_night=100, rating=4)]
    assert assign_labels(single)[0].labels == ["Cheapest", "Best rated"]
    assert assign_labels([HotelSuggestion(id="b", name="B")])[0].labels == []


def test_osm_amenity_mapping():
    assert osm_amenities({"internet_access": "wlan", "internet_access:fee": "no", "wheelchair": "yes"}) == [
        "Free Wi-Fi", "Wheelchair accessible"]


@pytest.mark.parametrize("check_out", [date(2026, 11, 1), date(2026, 10, 30), date(2026, 12, 5)])
def test_invalid_stay_dates_rejected(check_out):
    with pytest.raises(ValueError):
        HotelSearch(destination="Goa", check_in=date(2026, 11, 1), check_out=check_out)


@pytest.fixture
def client():
    app.state.hotel_suggestion_service = service()
    yield TestClient(app)
    del app.state.hotel_suggestion_service


def test_api_returns_suggestions(client):
    response = client.post("/hotels/suggestions", json={"destination": "Goa", "check_in": "2026-11-01",
                                                        "check_out": "2026-11-04", "adults": 2, "rooms": 1})
    assert response.status_code == 200
    assert len(response.json()["suggestions"]) == 3


def test_api_validation_and_destination_errors(client):
    bad = client.post("/hotels/suggestions", json={"destination": " ", "check_in": "2026-11-01", "check_out": "2026-11-04"})
    assert bad.status_code == 422
    app.state.hotel_suggestion_service = service(Providers(geocode_error=ProviderError("Destination not found.")))
    missing = client.post("/hotels/suggestions", json={"destination": "Nowhere", "check_in": "2026-11-01",
                                                        "check_out": "2026-11-04"})
    assert missing.status_code == 422 and missing.json()["detail"] == "Destination not found."


def test_existing_routes_still_registered(client):
    paths = set(client.get("/openapi.json").json()["paths"])
    assert {"/trips", "/trip", "/group-trips", "/hotels/suggestions"} <= paths
    assert get_hotel_service  # router helper remains importable


class FakeHTTP:
    def __init__(self, overpass=None, photon=None):
        self.overpass, self.photon, self.calls = overpass, photon, []

    def request(self, provider, method, url, **kwargs):
        self.calls.append(provider)
        reply = self.overpass if method == "POST" else self.photon
        if isinstance(reply, Exception):
            raise reply
        return reply, Source(provider=provider, status="live")


OVERPASS_HOTEL = {"elements": [{"type": "node", "id": 7, "lat": 26.9, "lon": 75.8,
                                "tags": {"name": "Hotel Pearl Palace", "tourism": "hotel", "stars": "3"}}]}
PHOTON_HOTEL = {"features": [{"geometry": {"coordinates": [75.8, 26.9]}, "properties": {
    "osm_id": 9, "osm_type": "N", "name": "Zostel Jaipur", "osm_key": "tourism", "osm_value": "hostel"}}]}


def test_lodging_finder_uses_targeted_overpass_query_first():
    http = FakeHTTP(overpass=OVERPASS_HOTEL)
    places, source = LodgingFinder(Providers(), http).find(26.9, 75.8)
    assert [p.name for p in places] == ["Hotel Pearl Palace"] and places[0].kind == "lodging"
    assert http.calls == ["OpenStreetMap / Overpass"]


def test_lodging_finder_falls_back_to_photon_then_general_search():
    http = FakeHTTP(overpass=ProviderError("Overpass timed out", retryable=True), photon=PHOTON_HOTEL)
    places, source = LodgingFinder(Providers(), http).find(26.9, 75.8)
    assert [p.name for p in places] == ["Zostel Jaipur"] and places[0].tags["tourism"] == "hostel"
    assert "Overpass timed out" in source.message

    providers = Providers()
    empty = FakeHTTP(overpass=ProviderError("down"), photon={"features": []})
    places, _ = LodgingFinder(providers, empty).find(26.9, 75.8)
    assert {p.name for p in places} == {"Sea View Hotel", "Budget Inn", "Palm Resort", "goa"}
    assert providers.discover_calls == 1
