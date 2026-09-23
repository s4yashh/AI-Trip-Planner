from datetime import date, datetime, timezone

import httpx
import pytest

from agents.live_agents import LiveBudgetAgent
from agents.live_orchestrator import LiveOrchestrator
from models.live import Allowances, Expense, HotelOffer, Place, Preferences, Route, Source, WeatherDay
from services.live_providers import LiveProviders, ProviderError, ProviderHTTP
from utils.opening_hours import windows


NOW = datetime(2026, 10, 1, 7, tzinfo=timezone.utc)


class FixtureProviders:
    """Test-only provider fixture. Never imported by application code."""
    rain = False
    closed = False

    def geocode(self, destination):
        return {"latitude": 26.9, "longitude": 75.8, "timezone": "Asia/Kolkata"}, Source(provider="fixture", status="live")

    def discover(self, latitude, longitude):
        return [Place(id=f"p{i}", name=f"Place {i}", kind="museum" if i % 2 else "park",
            latitude=26.9 + i/1000, longitude=75.8, opening_hours="off" if self.closed and i == 0 else "09:00-18:00",
            source=Source(provider="fixture", status="live")) for i in range(12)], Source(provider="fixture", status="live")

    def weather(self, prefs, latitude, longitude):
        return [WeatherDay(date=prefs.start_date, avoid_outdoor=self.rain)], Source(provider="fixture", status="live")

    def hotels(self, prefs, latitude, longitude):
        raise ProviderError("Hotel credentials missing")

    def route(self, first, second, mode, departure):
        return Route(from_id=first.id, to_id=second.id, minutes=20, source=Source(provider="fixture", status="live"))


def preferences(**kwargs):
    return Preferences(destination="Jaipur", start_date="2026-10-02", number_of_days=2, **kwargs)


def test_live_plan_schedules_known_places_with_unknown_budget():
    plan = LiveOrchestrator(FixtureProviders()).run(preferences(), now=NOW)
    assert plan.valid
    assert len(plan.activities) == 6
    assert plan.budget.total is None
    assert plan.budget.within_budget is None
    assert plan.sources["accommodation"].status == "unavailable"
    assert len({a.id for a in plan.activities}) == 6


def test_weather_changes_schedule_but_protects_locked_activity():
    provider = FixtureProviders()
    planner = LiveOrchestrator(provider)
    original = planner.run(preferences(), now=NOW)
    park = next(a for a in original.activities if a.place.kind == "park")
    park.locked = True
    provider.rain = True
    candidate = planner.run(preferences(), previous=original, now=NOW)
    preserved = next(a for a in candidate.activities if a.id == park.id)
    assert (preserved.date, preserved.start_time) == (park.date, park.start_time)
    assert not candidate.valid
    assert any("Weather" in message for message in candidate.conflicts)


def test_opening_change_removes_unlocked_activity():
    provider = FixtureProviders()
    planner = LiveOrchestrator(provider)
    original = planner.run(preferences(), now=NOW)
    provider.closed = True
    candidate = planner.run(preferences(), previous=original, now=NOW)
    assert candidate.valid
    assert all(a.id != "p0" for a in candidate.activities)


def test_budget_allowances_and_spending_are_not_double_counted():
    prefs = preferences(budget=600, allowances=Allowances(accommodation=100, transportation=100, food=100, activities=100, miscellaneous=0))
    budget = LiveBudgetAgent().run((prefs, [], [Expense(category="food", amount=120, description="Meals")]))
    assert budget.total == 420
    assert budget.spent == 120
    assert budget.remaining == 180
    assert budget.within_budget
    prefs.budget = 300
    plan = LiveOrchestrator(FixtureProviders()).run(prefs, now=NOW)
    assert not plan.valid
    assert plan.budget.within_budget is False


def test_currency_needs_explicit_rate(monkeypatch):
    hotel = HotelOffer(id="h", hotel_id="h", name="Hotel", amount=10, currency="USD", check_in="2026-10-02",
        check_out="2026-10-03", rooms=1, source=Source(provider="fixture"))
    monkeypatch.delenv("INR_PER_USD", raising=False)
    assert LiveBudgetAgent().run((preferences(), [hotel], [])).lines[0].planned is None
    monkeypatch.setenv("INR_PER_USD", "90")
    result = LiveBudgetAgent().run((preferences(), [hotel], []))
    assert result.lines[0].planned == 900
    assert "not a live" in result.conversion_note


def test_http_cache_and_rate_limit():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"data": [1]})
    service = ProviderHTTP(httpx.Client(transport=httpx.MockTransport(handler)))
    first = service.request("test", "GET", "https://example.test/")
    second = service.request("test", "GET", "https://example.test/")
    assert len(calls) == 1
    assert first[1].status == "live" and second[1].status == "cached"
    assert first[1].retrieved_at == second[1].retrieved_at
    limited = ProviderHTTP(httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(429))))
    with pytest.raises(ProviderError, match="rate limit"):
        limited.request("test", "GET", "https://example.test/")
    with pytest.raises(ProviderError, match="rate limited"):
        limited.request("test", "GET", "https://example.test/next")


def test_unknown_hours_and_closed_weekday():
    assert windows(None, date(2026, 10, 2)) is None
    assert windows("Mo-Fr 09:00-17:00; Sa-Su off", date(2026, 10, 3)) == []
    assert windows("Mo-Fr 09:00-17:00; PH off", date(2026, 10, 2)) is None


def test_providers_do_not_fill_absent_facts(monkeypatch):
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    monkeypatch.delenv("TOMTOM_API_KEY", raising=False)
    provider = LiveProviders()
    with pytest.raises(ProviderError, match="credentials"):
        provider.hotels(preferences(), 0, 0)
    with pytest.raises(ProviderError, match="forecast window"):
        provider.weather(Preferences(destination="Rome", start_date="2099-01-01"), 0, 0)
    first, second = FixtureProviders().discover(0, 0)[0][:2]
    route = provider.route(first, second, "walking")
    assert route.source.status == "estimated"
    assert route.traffic_delay_minutes is None


def test_overpass_parses_nodes_and_ways_without_fake_prices():
    def response(request):
        return httpx.Response(200, json={"elements": [
            {"type": "way", "id": 4, "center": {"lat": 10, "lon": 20}, "tags": {"name": "Museum", "tourism": "museum"}},
            {"type": "node", "id": 5, "lat": 10, "lon": 20, "tags": {"name": "Hospital", "amenity": "hospital", "phone": "+123"}},
        ]})
    providers = LiveProviders(ProviderHTTP(httpx.Client(transport=httpx.MockTransport(response))))
    places, source = providers.discover(10, 20)
    assert [p.id for p in places] == ["osm-way-4", "osm-node-5"]
    assert places[0].opening_hours is None
    assert places[1].phone == "+123"
    assert "rating" not in places[0].model_dump()


def test_amadeus_uses_production_and_full_stay_room_price(monkeypatch):
    monkeypatch.setenv("AMADEUS_CLIENT_ID", "test-id")
    monkeypatch.setenv("AMADEUS_CLIENT_SECRET", "test-secret")
    def response(request):
        assert request.url.host == "api.amadeus.com"
        if request.url.path.endswith("token"):
            return httpx.Response(200, json={"access_token": "token"})
        if request.url.path.endswith("by-geocode"):
            return httpx.Response(200, json={"data": [{"hotelId": "H1"}]})
        assert request.url.params["currency"] == "INR"
        return httpx.Response(200, json={"data": [{"available": True, "hotel": {"hotelId": "H1", "name": "Hotel"},
            "offers": [{"id": "O1", "price": {"total": "100", "currency": "INR"},
                        "checkInDate": "2026-10-02", "checkOutDate": "2026-10-03"}]}]})
    providers = LiveProviders(ProviderHTTP(httpx.Client(transport=httpx.MockTransport(response))))
    offers, _ = providers.hotels(preferences(rooms=2, travelers=3), 10, 20)
    assert offers[0].amount == 200


def test_tomtom_routes_include_provider_instructions(monkeypatch):
    monkeypatch.setenv("TOMTOM_API_KEY", "fixture-key")
    def response(request):
        assert request.url.params["traffic"] == "true"
        return httpx.Response(200, json={"routes": [{"summary": {
            "travelTimeInSeconds": 900, "lengthInMeters": 3000, "trafficDelayInSeconds": 120},
            "guidance": {"instructions": [{"message": "Turn right"}]}}]})
    providers = LiveProviders(ProviderHTTP(httpx.Client(transport=httpx.MockTransport(response))))
    first, second = FixtureProviders().discover(0, 0)[0][:2]
    route = providers.route(first, second, "driving")
    assert (route.minutes, route.traffic_delay_minutes) == (15, 2)
    assert route.instructions == ["Turn right"]


def test_place_failure_cannot_manufacture_an_itinerary():
    class NoPlaces(FixtureProviders):
        def discover(self, *args):
            raise ProviderError("Provider unavailable")
    plan = LiveOrchestrator(NoPlaces()).run(preferences(), now=NOW)
    assert not plan.valid and not plan.places and not plan.activities
    assert plan.sources["places"].status == "unavailable"


def test_weather_partial_coverage_and_missing_values():
    from datetime import timedelta
    today = date.today()
    def response(request):
        return httpx.Response(200, json={"daily": {"time": [today.isoformat()], "temperature_2m_max": [30]}})
    providers = LiveProviders(ProviderHTTP(httpx.Client(transport=httpx.MockTransport(response))))
    rows, source = providers.weather(Preferences(destination="Jaipur", start_date=today, number_of_days=30), 10, 20)
    assert len(rows) == 1 and source.status == "partial"
    assert rows[0].rain_probability is None
    assert rows[0].temperature_min is None


def test_expired_cache_refetches_and_server_errors_retry(monkeypatch):
    import services.live_providers as module
    clock = [10]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    calls = []
    def response(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"result": len(calls)})
    service = ProviderHTTP(httpx.Client(transport=httpx.MockTransport(response)))
    assert service.request("test", "GET", "https://example.test/", ttl=30)[0]["result"] == 2
    clock[0] = 41
    assert service.request("test", "GET", "https://example.test/", ttl=30)[0]["result"] == 3
