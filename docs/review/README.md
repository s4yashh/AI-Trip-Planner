# Project review materials

[Download the review PDF](../../output/pdf/AI_Trip_Planner_Review_Guide.pdf) or read the [editable guide](REVIEW_GUIDE.md).

The guide includes balanced speaking roles for two presenters, a twelve-minute presentation and demo plan, a reviewer inspection guide, example reviewer feedback, worked budget and revision examples, suggested answers with follow-up questions, and a repository evidence index. It describes application commit `bf85fdd`; update the baseline and recorded results when the implementation changes.

To rebuild the PDF, install the documentation-only dependency `reportlab` in your chosen Python environment, then run:

```powershell
python scripts/build_review_guide.py
```

The builder writes `output/pdf/AI_Trip_Planner_Review_Guide.pdf`. Explicit page breaks in the Markdown keep the speaking sections separate. After editing, render and inspect every page; update the page references on the opening page if pagination changes. Fonts use Arial when available on Windows and Helvetica otherwise.

## Controlled weather demonstration

Use this only as an explicitly labeled test demonstration. It uses fixture providers, a fixed test-model response, and a temporary database; it is not live travel information. Stop the normal frontend before starting this separate frontend session on the same port.

Backend terminal from the repository root:

```powershell
.\.venv\Scripts\python.exe -m tests.browser_server
```

Frontend terminal:

```powershell
$env:AI_BACKEND_URL='http://127.0.0.1:8001'
cd frontend
npm.cmd run dev -- --hostname 127.0.0.1
```

Create a test trip with a future outdoor visit, lock an indoor visit, and trigger the test weather change from another terminal:

```powershell
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/__test__/weather-change'
```

The harness advances its clock by 16 minutes and invokes monitoring. Inspect the itinerary and History after the visible browser poll. To return to normal, stop both test processes, remove the process-local override (`Remove-Item Env:AI_BACKEND_URL` in the frontend terminal), and restart the normal frontend. Never set the fixture address in committed application configuration.
