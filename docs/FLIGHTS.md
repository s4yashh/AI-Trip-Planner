# Flight search

The Flights page ([http://127.0.0.1:3000/flights](http://127.0.0.1:3000/flights)) collects the route, dates, passengers, cabin, and a direct-flight preference. It then opens a **pre-filled Skyscanner search** in a new tab. It is frontend-only, with no backend, database, or API key involved.

## Why there are no prices

Amadeus Self-Service closed on 17 July 2026, and no free flight-price API is available. Instead of showing invented or estimated fares, the page explains where to find each option on Skyscanner:
- **Cheapest**: Skyscanner's *Cheapest* tab.
- **Best (fastest / fewest stops)**: Skyscanner's *Best* and *Fastest* tabs.

All prices on Skyscanner are live.

## Details

- **Airport picker.** Suggestions come from a bundled list of about 140 major airports (`frontend/lib/airports.ts`). You can also type any 3-letter IATA code, or a city name that has a listed airport.
- **Link format.** `https://www.skyscanner.net/transport/flights/{from}/{to}/{yymmdd}[/{yymmdd}]/?adultsv2=N&cabinclass=…&rtn=0|1&preferdirects=true|false`.
- **Pre-fill.** The page accepts `?from=DEL&to=Goa&depart=YYYY-MM-DD&return=YYYY-MM-DD&adults=N`.
- **Children** are added on Skyscanner, because it needs each child's age.
