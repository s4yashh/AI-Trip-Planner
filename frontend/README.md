# AI Trip Planner — Frontend

A responsive web app that turns a destination, budget, number of days, and
travel interests into a personalized trip plan. The plans are generated live by
a Python multi-agent backend (recommendation, itinerary, and budget agents) that
runs separately from this app.

## Stack

- Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4
- No AI logic lives in this codebase — the frontend only renders what the backend returns

## How it works

1. The user fills in the trip form on `/plan`.
2. The browser calls the same-origin proxy route `app/api/trip/route.ts`.
3. The proxy forwards the request to the Python backend (`AI_BACKEND_URL`,
   default `http://localhost:8000`).
4. The backend runs the agents and returns a trip plan as JSON.
5. The frontend renders the recommended places, day-wise itinerary, budget
   analysis, and the real per-agent execution status.

## Getting started

```bash
# 1. Start the Python backend (from the repository root)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload        # serves http://localhost:8000

# 2. Start this app
cd frontend
npm install
npm run dev                          # serves http://localhost:3000
```

Open http://localhost:3000/plan and try e.g. Jaipur, 3 days, ₹30,000, with
History / Architecture / Culture interests.

## Environment variables

Copy `.env.example` to `.env.local` and adjust if needed:

- `NEXT_PUBLIC_API_URL` — override the browser-facing API URL (optional; the
  same-origin `/api/trip` proxy is the default).
- `AI_BACKEND_URL` — where the proxy forwards request to (default
  `http://localhost:8000`).

## Scripts

| Command           | Description                  |
| ----------------- | ---------------------------- |
| `npm run dev`     | Start the dev server         |
| `npm run build`   | Production build             |
| `npm start`       | Serve the production build   |
| `npm run lint`    | Lint with ESLint             |
| `npm test`        | Run the frontend unit tests  |

## Testing

Frontend tests use [Vitest](https://vitest.dev). They cover form validation,
interest selection, and the API client against mocked `fetch`.

```bash
npm test
```

## Deployment

Vercel-ready. Deploy with the root directory set to `frontend/` and define an
`AI_BACKEND_URL` environment variable pointing at your deployed FastAPI
backend. The INR→USD conversion used by the backend is a fixed prototype rate
(`INR_PER_USD`), not live data.

## Project structure

```
app/
  api/trip/route.ts   server proxy to the Python backend
  page.tsx            landing page
  plan/page.tsx       trip planner (form + results)
  about/page.tsx      how it works
components/           UI components (form, cards, status, loading)
lib/                  API client, validation, currency formatting
types/trip.ts         shared TypeScript types mirroring the API response
```