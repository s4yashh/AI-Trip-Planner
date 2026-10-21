# Hotel recommendations

Hotel suggestions are a separate, stateless feature. They do not change the single-trip or group-trip planners or their databases, and nothing is booked or stored.

## Where to find them

- **Hotels page** at [http://127.0.0.1:3000/hotels](http://127.0.0.1:3000/hotels): enter a destination, dates, guests, rooms, and currency.
- **Hotels tab** on any saved trip at `/plan`: the stay is pre-filled from the trip (check-in on the start date, `max(1, days - 1)` nights, travelers, rooms). This matches the planner's existing hotel convention.

Each search shows 3–5 hotels. Where the data allows, they carry the labels **Cheapest**, **Best rated**, and **Best value**. Each card shows the name, area and distance from the centre, price per night, rating, and key amenities, plus a **Book now** button. It opens Booking.com in a new tab, pre-filled with the hotel name, destination, check-in, check-out, guests, and rooms.

## Where the data comes from

Amadeus closed its Self-Service APIs on 17 July 2026, so no free hotel-price API is available. This feature therefore:

1. **Finds real hotels from OpenStreetMap.** It runs a lodging-only Overpass query, then a lodging-only Photon search, then the general place search as a last resort. Hotels named after the city itself are ignored.
2. **Optionally adds AI estimates.** If an assistant is configured (`LLM_PROVIDER` = `gemini` or `local`, as in the main README), it estimates the price per night for one room, a typical guest rating out of 5, and likely amenities. Every estimate is labelled **AI estimate**, and the page states that prices are approximate. Amenities and hotel-class stars from OpenStreetMap are shown as such and are never overwritten by AI estimates.
3. **Works without an assistant.** Without one, the cards show real names and booking links with "Price: check on the booking site". No prices are invented.
4. **Falls back to the AI if no map listings are available.** If no OpenStreetMap listings are available, the assistant may suggest well-known hotels. These are marked **Unverified AI suggestion**.

There is no scraping. Live prices and availability are only on the booking site.

Labels are computed only from available values. Cheapest needs prices. Best rated uses the highest rating. Best value balances rating against price and prefers a third, distinct hotel when it is nearly as good a deal.

The page shows the location the geocoder resolved (e.g. "Jaipur, Rajasthan, India"). Some ambiguous names resolve to the wrong place in the shared Open-Meteo geocoder (e.g. "Goa"), so check that line.

When Gemini is used, the destination, dates, guest counts, and OpenStreetMap hotel names are sent to Google for estimation.

## API

- `POST /hotels/suggestions` with `{destination, check_in, check_out, adults, rooms, currency}`. Check-out must be 1–30 nights after check-in.

The Next.js page proxies this endpoint through `/api/hotels/suggestions`. Results are cached in memory for 30 minutes per search.
