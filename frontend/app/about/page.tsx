const AGENTS = [
  {
    number: "01",
    name: "Recommendation Agent",
    tone: "from-[#0b3954] to-[#0f766e]",
    detail:
      "Scores every place in the dataset against your selected interests using text-feature similarity (TF-IDF with cosine similarity), then ranks the best matches above the rest — with a plain-language reason for each pick.",
  },
  {
    number: "02",
    name: "Itinerary Agent",
    tone: "from-[#0f766e] to-[#14b8a6]",
    detail:
      "Schedules the top ranked places into a day-wise plan with start and end times, respecting visit durations and up to four places per day, and skipping places that do not fit any day.",
  },
  {
    number: "03",
    name: "Budget Agent",
    tone: "from-[#f26b4f] to-[#dd5944]",
    detail:
      "Estimates the total trip cost across accommodation, transport, food, activities and miscellaneous, compares it against your budget, and suggests concrete ways to stay within it.",
  },
];

const FUTURE_WORK = [
  "Flights and hotels with live pricing",
  "Weather-aware scheduling",
  "Real-time currency conversion",
  "User accounts and trip history",
  "Image galleries for destinations",
  "PDF export of itineraries",
];

const FLOW = [
  { label: "Next.js frontend", value: "/api/trip →" },
  { label: "FastAPI boundary", value: "/trip →" },
  { label: "Orchestrator", value: "3 agents →" },
  { label: "Plan JSON", value: "results" },
];

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-14 sm:px-6">
      <div className="relative overflow-hidden rounded-3xl bg-[#17233d] px-8 py-12 text-white shadow-xl shadow-slate-900/15">
        <div className="travel-grid absolute inset-0 opacity-40" aria-hidden="true" />
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-[#f26b4f]/25 blur-3xl" aria-hidden="true" />
        <p className="relative text-xs font-semibold uppercase tracking-widest text-[#ffb08e]">
          About the project
        </p>
        <h1 className="relative mt-2 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
          How It Works
        </h1>
        <p className="relative mt-4 max-w-2xl text-slate-300">
          Instead of a single model producing a whole plan, three specialised
          agents each own one piece of the problem and an orchestrator wires
          their outputs together into a single trip plan.
        </p>
      </div>

      <section className="mt-12">
        <div className="mb-5 flex items-center gap-3">
          <span className="h-px w-6 bg-[#f26b4f]" aria-hidden="true" />
          <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900">
            The agents
          </h2>
        </div>
        <div className="space-y-4">
          {AGENTS.map((agent) => (
            <div
              key={agent.name}
              className="group overflow-hidden rounded-2xl border border-[#e9e2d3] bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lg"
            >
              <div className="flex items-center gap-3.5">
                <span
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${agent.tone} font-display text-base font-semibold text-white shadow-md`}
                >
                  {agent.number}
                </span>
                <h3 className="text-lg font-bold text-slate-900">{agent.name}</h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">
                {agent.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-12">
        <div className="mb-5 flex items-center gap-3">
          <span className="h-px w-6 bg-[#f26b4f]" aria-hidden="true" />
          <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900">
            How a request flows
          </h2>
        </div>
        <ol className="flex flex-wrap items-center gap-2">
          {FLOW.map((step) => (
            <li
              key={step.label}
              className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm shadow-sm"
            >
              <span className="font-semibold text-slate-800">{step.label}</span>
              <span className="text-teal-700">{step.value}</span>
            </li>
          ))}
        </ol>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">
          The browser calls the Next.js <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">/api/trip</code>{" "}
          proxy route, which forwards to a Python FastAPI service. That service
          runs the orchestrator, which coordinates the three agents and returns
          the finished plan as JSON. The frontend renders the plan and the real
          per-agent execution status — nothing in the UI fabricates results.
        </p>
      </section>

      <section className="mt-12">
        <div className="mb-5 flex items-center gap-3">
          <span className="h-px w-6 bg-amber-500" aria-hidden="true" />
          <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900">
            Planned next
          </h2>
        </div>
        <p className="max-w-2xl text-sm text-slate-600">
          These features are scoped but not yet implemented:
        </p>
        <ul className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {FUTURE_WORK.map((item) => (
            <li
              key={item}
              className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm"
            >
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600" aria-hidden="true">
                <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M12 9v4M12 17h.01" />
                  <path d="M10.3 3.6 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0z" />
                </svg>
              </span>
              {item}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
