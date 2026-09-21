import type { AgentExecutionStatus } from "@/types/trip";

const LABELS: { key: keyof AgentExecutionStatus; label: string }[] = [
  { key: "poi_recommendation", label: "Recommendation agent" },
  { key: "itinerary", label: "Itinerary agent" },
  { key: "budget", label: "Budget agent" },
];

export function AgentStatus({ status }: { status: AgentExecutionStatus }) {
  const agents = LABELS.filter((item) => typeof status[item.key] === "boolean");

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2">
        <h3 className="text-base font-semibold text-slate-900">Agent Status</h3>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
            status.orchestrator
              ? "bg-emerald-50 text-emerald-700"
              : "bg-red-50 text-red-700"
          }`}
        >
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: "currentColor" }}
            aria-hidden="true"
          />
          {status.orchestrator ? "All agents completed" : "Some agents failed"}
        </span>
      </div>

      <ul className="mt-4 space-y-2">
        {agents.map(({ key, label }) => (
          <li key={key} className="flex items-center justify-between text-sm">
            <span className="text-slate-700">{label}</span>
            <span
              className={`inline-flex items-center gap-1.5 pl-3 font-medium ${
                status[key] ? "text-emerald-700" : "text-red-700"
              }`}
            >
              <span
                className="flex h-4 w-4 items-center justify-center rounded-full text-xs"
                style={{
                  backgroundColor: status[key] ? "#ecfdf5" : "#fef2f2",
                  color: status[key] ? "#047857" : "#b91c1c",
                }}
                aria-hidden="true"
              >
                {status[key] ? "\u2713" : "\u2715"}
              </span>
              {status[key] ? "Succeeded" : "Failed"}
            </span>
          </li>
        ))}
      </ul>

      <div className="mt-4 rounded-lg bg-slate-50 p-3">
        <p className="text-xs font-medium text-slate-500">What happened</p>
        <ul className="mt-1.5 space-y-1">
          {status.lines.map((line) => (
            <li key={line} className="text-sm text-slate-700">
              &middot; {line}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}