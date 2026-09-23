"""Production data adapters. No sample responses and no synthetic provider facts."""
import copy
import math
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

import httpx

from models.live import HotelOffer, Place, Preferences, Route, Source, WeatherDay, utcnow
from services.routing_service import haversine_km


class ProviderError(Exception):
    pass


class ProviderHTTP:
    """Bounded network calls, expiring cache, and host-wide rate-limit backoff."""
    def __init__(self, client=None):
        self.client = client or httpx.Client(timeout=httpx.Timeout(15, connect=5), follow_redirects=False)
        self.cache = {}
        self.backoff = {}
        self.lock = threading.RLock()

    def request(self, provider, method, url, *, ttl=900, **kwargs):
        # Cache keys stay in memory and are never logged (they can contain credentials).
        key = (method, url, repr(kwargs))
        with self.lock:
            cached = self.cache.get(key)
            if cached and cached[0] > time.monotonic():
                data, source = copy.deepcopy(cached[1:])
                source.status = "cached"
                return data, source
            host = httpx.URL(url).host
            if self.backoff.get(host, 0) > time.monotonic():
                raise ProviderError(f"{provider} is temporarily rate limited; retry later.")
        for attempt in range(2):
            try:
                response = self.client.request(method, url, **kwargs)
                if response.status_code == 429:
                    try:
                        seconds = max(60, min(3600, int(response.headers.get("Retry-After", "60"))))
                    except ValueError:
                        seconds = 60
                    with self.lock:
                        self.backoff[host] = time.monotonic() + seconds
                    raise ProviderError(f"{provider} rate limit reached; retry after {seconds} seconds.")
                if response.status_code >= 500 and attempt == 0:
                    time.sleep(0.2)
                    continue
                response.raise_for_status()
                data = response.json()
                source = Source(provider=provider, status="live", retrieved_at=utcnow(),
                                expires_at=(datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat())
                with self.lock:
                    if len(self.cache) >= 512:
                        self.cache = {k: v for k, v in self.cache.items() if v[0] > time.monotonic()}
                        if len(self.cache) >= 512:
                            self.cache.pop(next(iter(self.cache)))
                    self.cache[key] = (time.monotonic() + ttl, copy.deepcopy(data), source.model_copy())
                return data, source
            except httpx.HTTPStatusError as exc:
                raise ProviderError(f"{provider} returned HTTP {exc.response.status_code}.") from exc
            except (httpx.RequestError, ValueError) as exc:
                if attempt == 0:
                    time.sleep(0.2)
                    continue
                raise ProviderError(f"{provider} unavailable ({type(exc).__name__}).") from exc
        raise ProviderError(f"{provider} unavailable.")


class LiveProviders:
    def __init__(self, http=None):
        self.http = http or ProviderHTTP()

    def geocode(self, destination):
        payload, source = self.http.request("Open-Meteo geocoding", "GET",
            "https://geocoding-api.open-meteo.com/v1/search", ttl=86400,
            params={"name": destination, "count": 1, "language": "en", "format": "json"})
        results = payload.get("results") or []
        if not results:
            raise ProviderError("Destination not found. Try a city name and country.")
        return results[0], source

    def discover(self, latitude, longitude):
        radius = 6000
        around = f"(around:{radius},{float(latitude)},{float(longitude)})"
        query = ('[out:json][timeout:12];('
            f'nwr["tourism"~"^(attraction|museum|gallery|viewpoint|zoo|theme_park|hotel|hostel|guest_house)$"]{around};'
            f'nwr["historic"]{around};nwr["leisure"="park"]{around};'
            f'nwr["amenity"~"^(restaurant|cafe|hospital|pharmacy|police)$"]{around};'
            ');out center tags 400;')
        payload, source = self.http.request("OpenStreetMap / Overpass", "POST",
            os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter"),
            ttl=1800, data={"data": query})
        places = []
        for element in payload.get("elements", []):
            tags = element.get("tags", {})
            coords = element.get("center", element)
            if not tags.get("name") or coords.get("lat") is None or coords.get("lon") is None:
                continue
            if tags.get("disused") == "yes" or tags.get("access") in {"private", "no"}:
                continue
            amenity, tourism = tags.get("amenity"), tags.get("tourism")
            kind = (amenity if amenity in {"hospital", "pharmacy", "police", "restaurant", "cafe"}
                    else "lodging" if tourism in {"hotel", "hostel", "guest_house"}
                    else tourism or ("historic" if tags.get("historic") else "park"))
            places.append(Place(id=f"osm-{element['type']}-{element['id']}", name=tags["name"], kind=kind,
                latitude=coords["lat"], longitude=coords["lon"], tags=tags,
                opening_hours=tags.get("opening_hours"), phone=tags.get("contact:phone") or tags.get("phone"),
                website=tags.get("website") or tags.get("contact:website"), source=source))
        return places, source

    def weather(self, prefs: Preferences, latitude, longitude):
        today = datetime.now(timezone.utc).date()
        last = today + timedelta(days=15)
        trip_end = prefs.start_date + timedelta(days=prefs.number_of_days - 1)
        start, end = max(today, prefs.start_date), min(last, trip_end)
        if start > end:
            raise ProviderError("Trip dates are outside the available 16-day forecast window.")
        payload, source = self.http.request("Open-Meteo weather", "GET",
            "https://api.open-meteo.com/v1/forecast", ttl=1800, params={
                "latitude": latitude, "longitude": longitude, "timezone": "auto",
                "start_date": start.isoformat(), "end_date": end.isoformat(),
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
            })
        daily = payload.get("daily", {})
        days = []
        for i, day in enumerate(daily.get("time", [])):
            def value(key):
                values = daily.get(key) or []
                return values[i] if i < len(values) else None
            rain, wind = value("precipitation_probability_max"), value("wind_speed_10m_max")
            days.append(WeatherDay(date=day, temperature_min=value("temperature_2m_min"),
                temperature_max=value("temperature_2m_max"), rain_probability=rain, wind_kmh=wind,
                avoid_outdoor=(rain is not None and rain >= 60) or (wind is not None and wind >= 45)))
        if len(days) < prefs.number_of_days:
            source.status = "partial"
            source.message = "Weather is only available for part of this trip; other dates are unknown."
        return days, source

    def hotels(self, prefs, latitude, longitude):
        client_id, secret = os.getenv("AMADEUS_CLIENT_ID"), os.getenv("AMADEUS_CLIENT_SECRET")
        if not client_id or not secret:
            raise ProviderError("Hotel prices unavailable: configure Amadeus production credentials.")
        base = "https://api.amadeus.com"
        token, _ = self.http.request("Amadeus authentication", "POST", base + "/v1/security/oauth2/token",
            ttl=900, data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret})
        headers = {"Authorization": "Bearer " + token["access_token"]}
        listing, _ = self.http.request("Amadeus hotels", "GET", base + "/v1/reference-data/locations/hotels/by-geocode",
            ttl=86400, headers=headers, params={"latitude": latitude, "longitude": longitude, "radius": 10})
        ids = [hotel["hotelId"] for hotel in listing.get("data", [])][:20]
        if not ids:
            return [], Source(provider="Amadeus hotels", status="live", retrieved_at=utcnow(), message="No hotels found nearby.")
        checkout = prefs.start_date + timedelta(days=max(1, prefs.number_of_days - 1))
        payload, source = self.http.request("Amadeus hotel offers", "GET", base + "/v3/shopping/hotel-offers",
            ttl=900, headers=headers, params={"hotelIds": ",".join(ids), "adults": math.ceil(prefs.travelers / prefs.rooms),
                "roomQuantity": prefs.rooms, "checkInDate": prefs.start_date.isoformat(),
                "checkOutDate": checkout.isoformat(), "currency": prefs.currency, "bestRateOnly": "true"})
        offers = []
        for row in payload.get("data", []):
            if row.get("available") is False:
                continue
            for offer in row.get("offers", []):
                offers.append(HotelOffer(id=offer["id"], hotel_id=row["hotel"]["hotelId"], name=row["hotel"]["name"],
                    amount=round(float(offer["price"]["total"]) * prefs.rooms, 2), currency=offer["price"]["currency"],
                    check_in=offer["checkInDate"], check_out=offer["checkOutDate"], rooms=prefs.rooms, source=source))
        return offers, source

    def route(self, first: Place, second: Place, mode, departure=None):
        key = os.getenv("TOMTOM_API_KEY")
        if not key:
            distance = haversine_km((first.latitude, first.longitude), (second.latitude, second.longitude))
            return Route(from_id=first.id, to_id=second.id, distance_km=round(distance, 2),
                minutes=round(distance * 1.4 / (4.5 if mode == "walking" else 25) * 60, 1),
                source=Source(provider="Geographic estimate", status="estimated", retrieved_at=utcnow(),
                    message="Straight-line distance × 1.4, at 4.5 km/h walking or 25 km/h driving. No road or traffic data."))
        locations = f"{first.latitude},{first.longitude}:{second.latitude},{second.longitude}"
        params = {"key": key, "travelMode": "pedestrian" if mode == "walking" else "car",
                  "traffic": "true" if mode == "driving" else "false", "instructionsType": "text", "language": "en-US"}
        if departure and mode == "driving":
            params["departAt"] = departure
        payload, source = self.http.request("TomTom routing", "GET",
            f"https://api.tomtom.com/routing/1/calculateRoute/{quote(locations, safe=',:')}/json",
            ttl=900, params=params)
        routes = payload.get("routes") or []
        if not routes:
            raise ProviderError("TomTom found no route between these activities.")
        route = routes[0]
        summary = route["summary"]
        delay = summary.get("trafficDelayInSeconds") if mode == "driving" else None
        return Route(from_id=first.id, to_id=second.id, minutes=round(summary["travelTimeInSeconds"] / 60, 1),
            distance_km=round(summary["lengthInMeters"] / 1000, 2),
            traffic_delay_minutes=round(delay / 60, 1) if delay is not None else None,
            instructions=[step["message"] for step in route.get("guidance", {}).get("instructions", []) if step.get("message")],
            source=source)
