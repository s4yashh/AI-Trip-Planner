# Adaptive Multi-Agent AI Trip Planner

A persistent local FastAPI + Next.js application with live-data planning agents, automatic itinerary updates, expense tracking, and your choice of an existing local model or Google Gemini. No runtime demo data or model installation/downloads.

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

To use Gemini instead, set `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, and `GEMINI_MODEL` in the root `.env`, then restart the backend. The key stays on the backend; Gemini conversations send relevant trip context to Google. Keep keys out of Git. Switch back with `LLM_PROVIDER=local`.

See [the configuration and architecture guide](docs/GUIDE.md) for provider setup, budget semantics, API contracts, persistence, monitoring, and limitations. See [verification results](VERIFICATION.md) for test evidence.

For project review, use the [PDF review guide](output/pdf/AI_Trip_Planner_Review_Guide.pdf), with speaking roles for two presenters, a demo runbook, reviewer prompts, and follow-up questions. Its [editable source and rebuild instructions](docs/review/README.md) are included.

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
