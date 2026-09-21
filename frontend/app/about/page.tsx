const AGENTS = [
  {
    name: "Recommendation Agent",
    detail:
      "Scores every place in the dataset against your selected interests using text-feature similarity (TF-IDF with cosine similarity), then ranks the best matches above the rest.",
  },
  {
    name: "Itinerary Agent",
    detail:
      "Schedules the top ranked places into a day-wise plan with start and end times, respecting visit durations and <=4 places per day, and skipping places that do not fit any day.",
  },
  {
    name: "Budget Agent",
    detail:
      "Estimates the total trip cost (accommodation, transport, food, activities, miscellaneous), compares it with your budget, and suggests concrete ways to stay within it.",
  },
];

const FUTURE_WORK = [
  "Flight and hotel availability, with live pricing",
  "Weather-aware scheduling",
  "Real-time currency conversion",
  "User accounts and trip history",
  "Image galleries for destinations",
  "PDF export of itineraries",
];

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <h1 className="text-3xl font-bold tracking-tight text-slate-900">
        How It Works
      </h1>
      <p className="mt-3 text-slate-600">
        This project explores a multi-agent approach to trip planning. Instead
        of a single model producing a whole plan, three specialised agents each
        own one piece of the problem and an orchestrator wires their outputs
        together.
      </p>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-slate-900">The Agents</h2>
        <div className="mt-4 space-y-4">
          {AGENTS.map((agent, index) => (
            <div
              key={agent.name}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-sm font-semibold text-white">
                  {index + 1}
                </span>
                <h3 className="font-semibold text-slate-900">{agent.name}</h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">
                {agent.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-slate-900">Architecture</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          The Next.js frontend calls its own <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">/api/trip</code>{" "}
          proxy route, which forwards the request to a Python FastAPI service.
          That service runs the orchestrator, which coordinates the three
          agents and returns the finished plan as JSON. The frontend renders
          the plan and the real per-agent execution status &mdash; nothing in
          the UI fabricates results.
        </p>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-slate-900">Planned Next</h2>
        <p className="mt-2 text-sm text-slate-600">
          These features are scoped but not yet implemented:
        </p>
        <ul className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {FUTURE_WORK.map((item) => (
            <li
              key={item}
              className="flex items-center gap-2 text-sm text-slate-600"
            >
              <span className="text-amber-500" aria-hidden="true">
                &bull;
              </span>
              {item}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}