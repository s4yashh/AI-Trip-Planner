# Adaptive Multi-Agent AI Trip Planner

A persistent local FastAPI + Next.js application with live-data planning agents, automatic itinerary updates, expense tracking, and an existing local OpenAI-compatible model connection. No runtime demo data or model installation/downloads.

## Windows setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
cd frontend
npm.cmd ci
cd ..
```

In two terminals, run `.\run.ps1 backend` and `.\run.ps1 frontend`. Open http://127.0.0.1:3000/plan. Requires Python 3.11+ and Node.js 20.9+. Keep the backend running for automatic updates.

Set `LOCAL_LLM_MODEL` and `LOCAL_LLM_BASE_URL` in `.env` to connect to an already loaded model. The form works without a model. Optional Amadeus production credentials enable hotel quotes; a TomTom key enables routing and traffic. Missing information stays unavailable.

See [the configuration and architecture guide](docs/GUIDE.md) for provider setup, budget semantics, API contracts, persistence, monitoring, and limitations. See [verification results](VERIFICATION.md) for test evidence.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm.cmd test
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd run build
```

Sample data and mocked services are isolated under `tests/`. The application starts with no seeded trips. This is a single-user local app; accounts, bookings, payments, flights, and public deployment are outside its scope.
