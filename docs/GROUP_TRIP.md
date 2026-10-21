# Group trip planning

Group planning is a separate workflow at `/group-plan`; it does not change the existing `/plan` workflow or its database. Group records are stored in `data/group_trips.sqlite3` (or the optional `GROUP_TRIP_DB_PATH`).

## Run and demo

Start the app using the same local run instructions in the main README, then open [http://127.0.0.1:3000/group-plan](http://127.0.0.1:3000/group-plan).

**Quickest demo:** click **Try a demo group (3 members)**. It creates the group below and saves each member's preferences. Then click **Generate fair group itinerary**.

| Member | Budget cap | Interests, in priority order | Pace |
| --- | ---: | --- | --- |
| Asha | ₹6,000 | beach, food, market | relaxed |
| Ravi | ₹3,500 | trek, nature, viewpoint | packed |
| Meera | ₹9,000 | history, architecture, museum | moderate |

Destination: Kochi, India, for 3 days, starting 5 days from today, in INR. The demo data lives in `frontend/lib/group-demo.ts`. To enter it by hand, create the group with those names and fill in each member card.

These choices are deliberately at odds: beach vs trek vs history, relaxed vs packed, and ₹3,500 vs ₹9,000. The result shows:
- **Why this plan**: written by the configured AI assistant, or by the planner's rules when no assistant is set.
- **Day-split itinerary**: each day shows who it is for, its focus, and its pace.
- **Conflicts found and how they were resolved.**
- **Costs and budget flags**: known costs, plus an *approximate* shared-stay cost when the AI can estimate hotel prices, with per-member flags.
- **Links**: pre-filled Hotels and Flights searches for the whole group.

Avoid "Goa" for now. The shared geocoder resolves it to the wrong place (see `docs/HOTELS.md`).

## How conflicts are resolved: splitting days

The default planner is `GroupDaySplitAgent` (`agents/group_day_split_agent.py`). It extends the original `GroupTripAgent`, which is unchanged:

1. **Every top interest gets a themed day.** Members who share a top interest share the day. When there are more themes than days, themes share a day and alternate slots. Spare days go to second interests, then to shared "best for everyone" days.
2. **Each themed day runs at its featured members' pace.** For example, Asha's beach day is relaxed and Ravi's day is packed. The whole trip is not forced into one middle pace.
3. **Weather.** If rain is forecast, outdoor-heavy themes move to dry days and indoor-friendly themes (museums) take the rainy ones.
4. **Missing places.** If live data has no places for a theme (e.g. "trek"), that member's day uses their next interest that does have places. A planning note says so.
5. **Reserved places.** Each themed day's best places are held back from earlier days, and leftover slots go to the strongest whole-group matches.
6. **Budget.** Members with very different budgets are compared against an equal share. The approximate shared stay uses the cheapest suggested hotel, two people per room, to protect the tightest budget.

Member names are optional when creating a group. Blank names become "Member N". Groups and plans saved before this change still load, because the new fields are optional.

## Budget meaning

Personal budgets are caps, not estimates of what a member will spend. Known itinerary costs are split equally for comparison. If required cost categories or provider prices are missing, the group page labels the total and per-member figure as an incomplete known-cost lower bound; it does not claim that the trip is affordable. Unknown activity prices are not invented.

## Scope and API

This local version stores distinct member submissions in the same group workspace; it has no accounts or remote invitation links. It uses the existing live geocoding, place, weather, accommodation, and route providers. If both Overpass instances fail transiently, a bounded Photon/OpenStreetMap search is attempted. Provider outages may still leave some interests uncovered; the page reports those gaps rather than fabricating places.

The group-only API is registered under `/group-trips`:

- `POST /group-trips` — create the group and its member slots (optional `member_names`).
- `GET /group-trips/{id}` — reload a saved group.
- `PATCH /group-trips/{id}/members/{member_id}` — save one member's preferences.
- `POST /group-trips/{id}/plan` — generate and save the shared plan.

The standalone Next.js page proxies these requests through `/api/group-trips`; the existing single-trip proxy and API routes are unchanged.
