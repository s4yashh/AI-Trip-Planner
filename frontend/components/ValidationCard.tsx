import type { ValidationReport } from "@/types/trip";

interface ValidationCardProps {
  validation: ValidationReport;
}

export function ValidationCard({ validation }: ValidationCardProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-[#e9e2d3] bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-[#eee9df] px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-900">
            Validation &amp; re-planning
          </h3>
          <p className="text-sm text-slate-500">
            Every plan is checked before it is shown —{" "}
            {validation.attempts} of {validation.max_attempts} attempt
            {validation.max_attempts === 1 ? "" : "s"} used.
          </p>
        </div>
        <span
          className={`inline-flex items-center gap-2 self-start rounded-xl px-3.5 py-2 text-sm font-bold ${
            validation.passed
              ? "bg-teal-50 text-teal-700"
              : "bg-red-50 text-red-700"
          }`}
        >
          {validation.passed ? "All checks passed" : "Checks failed"}
        </span>
      </div>
      <div className="space-y-3 px-6 py-5">
        {validation.notes.length > 0 ? (
          <div className="rounded-xl border border-teal-100 bg-teal-50/60 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
              How the plan was refined
            </p>
            <ul className="mt-1.5 space-y-1">
              {validation.notes.map((note) => (
                <li key={note} className="text-sm text-slate-700">
                  → {note}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {validation.violations.length > 0 ? (
          <div className="rounded-xl border border-red-100 bg-red-50/60 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
              Remaining issues
            </p>
            <ul className="mt-1.5 space-y-1">
              {validation.violations.map((violation) => (
                <li key={`${violation.code}-${violation.message}`} className="text-sm text-slate-700">
                  <span className="font-mono text-xs font-bold text-red-600">
                    [{violation.code}]
                  </span>{" "}
                  {violation.message}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}
