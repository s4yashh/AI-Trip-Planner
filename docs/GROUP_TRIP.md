# Group trip planning

Group planning is a separate workflow at `/group-plan`; it does not change the existing `/plan` workflow or its database. Group records are stored in `data/group_trips.sqlite3` (or the optional `GROUP_TRIP_DB_PATH`).

## Run and demo

Start the app using the same local run instructions in the main README, then open [http://127.0.0.1:3000/group-plan](http://127.0.0.1:3000/group-plan).

1. Create a group for Goa, India, for 4 days, with 3 members and INR currency.
2. Have each member fill and save their own card:

   | Member | Budget cap | Interests, in priority order | Pace |
   | --- | ---: | --- | --- |
   | Member 1 | ₹6,000 | beach, local food, market | relaxed |
   | Member 2 | ₹3,500 | trek, nature, viewpoint | packed |
   | Member 3 | ₹5,000 | history, architecture, food | moderate |

3. Generate the itinerary. Review the per-member interest coverage, the detected interest/pace/budget conflicts, their resolutions, and the equal-share budget checks.

The first interest in each member's list is treated as their top interest. Candidate activities are ranked against each member and selected in a fair rotation before scheduling. The combined daily pace is the median of submitted paces. When member interests differ, member-matched activities are prioritized; conflicts that live place data cannot satisfy remain visibly unresolved.

## Budget meaning

Personal budgets are caps, not estimates of what a member will spend. Known itinerary costs are split equally for comparison. If required cost categories or provider prices are missing, the group page labels the total and per-member figure as an incomplete known-cost lower bound; it does not claim that the trip is affordable. Unknown activity prices are not invented.

## Scope and API

This local version stores distinct member submissions in the same group workspace; it has no accounts or remote invitation links. It uses the existing live geocoding, place, weather, accommodation, and route providers. If both Overpass instances fail transiently, a bounded Photon/OpenStreetMap search is attempted. Provider outages may still leave some interests uncovered; the page reports those gaps rather than fabricating places.

The group-only API is registered under `/group-trips`:

- `POST /group-trips` — create the group and its member slots.
- `GET /group-trips/{id}` — reload a saved group.
- `PATCH /group-trips/{id}/members/{member_id}` — save one member's preferences.
- `POST /group-trips/{id}/plan` — generate and save the shared plan.

The standalone Next.js page proxies these requests through `/api/group-trips`; the existing single-trip proxy and API routes are unchanged.
