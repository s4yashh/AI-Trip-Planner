import type { AgentExecutionStatus } from "@/types/trip";

const LABELS: { key: keyof AgentExecutionStatus; label: string; detail: string }[] = [
  { key: "poi_recommendation", label: "Recommendation agent", detail: "Rank places against your interests" },
  { key: "itinerary", label: "Itinerary agent", detail: "Schedule each day of the trip" },
  { key: "budget", label: "Budget agent", detail: "Estimate costs and compare with budget" },
];

export function AgentStatus({ status }: { status: AgentExecutionStatus }) {
  const okCount = Object.values(status).filter((value) => value === true).length;

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-slate-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Agent Status</h3>
          <p className="text-sm text-slate-500">
            How the plan was built — live status from the backend.
          </p>
        </div>
        <span
          className={`inline-flex items-center gap-2 self-start rounded-xl px-3.5 py-2 text-sm font-bold ${
            status.orchestrator && okCount === 4
              ? "bg-emerald-50 text-emerald-700"
              : "bg-amber-50 text-amber-700"
          }`}
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60" style={{ backgroundColor: "currentColor" }} aria-hidden="true" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "currentColor" }} aria-hidden="true" />
          </span>
          {status.orchestrator && okCount === 4
            ? "All agents completed"
            : "Partially completed"}
        </span>
      </div>

      <div className="px-6 py-5">
        <ul className="space-y-2.5">
          {LABELS.map(({ key, label, detail }) => {
            const succeeded = status[key] === true;
            return (
              <li
                key={key}
                className={`flex items-center gap-3.5 rounded-xl border px-4 py-3 transition-colors ${
                  succeeded
                    ? "border-emerald-100 bg-emerald-50/50"
                    : "border-red-100 bg-red-50/50"
                }`}
              >
                <span
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                    succeeded
                      ? "bg-emerald-600 text-white"
                      : "bg-red-500 text-white"
                  }`}
                  aria-hidden="true"
                >
                  {succeeded ? (
                    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                      <path d="M18 6 6 18M6 6l12 12" />
                    </svg>
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold text-slate-900">{label}</p>
                  <p className="text-xs text-slate-500">{detail}</p>
                </div>
                <span
                  className={`shrink-0 text-xs font-bold uppercase tracking-wide ${
                    succeeded ? "text-emerald-700" : "text-red-600"
                  }`}
                >
                  {succeeded ? "Done" : "Failed"}
                </span>
              </li>
            );
          })}
        </ul>

        <div className="mt-5 rounded-xl bg-slate-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            What happened
          </p>
          <ul className="mt-1.5 space-y-1">
            {status.lines.map((line) => (
              <li key={line} className="text-sm text-slate-700">
                {line}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}