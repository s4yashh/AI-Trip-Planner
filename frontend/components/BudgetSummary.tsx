import { formatMoney } from "@/lib/money";
import type { BudgetAnalysis, BudgetLine } from "@/types/trip";

interface BudgetSummaryProps {
  analysis: BudgetAnalysis;
  currency: string;
}

const SEGMENT_COLORS: Record<string, string> = {
  Accommodation: "bg-[#0f766e]",
  Transportation: "bg-[#0b3954]",
  Food: "bg-[#f26b4f]",
  Activities: "bg-[#d7a736]",
  Miscellaneous: "bg-slate-300",
};

const BREAKDOWN_ORDER = ["Accommodation", "Transportation", "Food", "Activities", "Miscellaneous"];

export function BudgetSummary({ analysis, currency }: BudgetSummaryProps) {
  const { within_budget } = analysis;
  const total = analysis.total_cost || 0;

  function segmentFor(line: BudgetLine) {
    const amount = line.amount || 0;
    return {
      ...line,
      color: SEGMENT_COLORS[line.category] ?? "bg-slate-300",
      percent: total > 0 ? (amount / total) * 100 : 0,
    };
  }

  const sortedLines = [...analysis.breakdown]
    .sort((a, b) => {
      const ia = BREAKDOWN_ORDER.indexOf(a.category);
      const ib = BREAKDOWN_ORDER.indexOf(b.category);
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    })
    .map(segmentFor);

  return (
    <div className="overflow-hidden rounded-2xl border border-[#e9e2d3] bg-white shadow-sm">
      <div className="flex flex-col gap-4 border-b border-[#eee9df] px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Budget Analysis</h3>
          <p className="text-sm text-slate-500">
            {within_budget === null
              ? "No budget provided — showing the estimated total."
              : "Estimated against the budget you set."}
          </p>
        </div>
        {within_budget !== null ? (
          <span
            className={`inline-flex items-center gap-2 self-start rounded-xl px-3.5 py-2 text-sm font-bold ${
              within_budget
                ? "bg-teal-50 text-teal-700"
                : "bg-red-50 text-red-700"
            }`}
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              {within_budget ? (
                <path d="M20 6 9 17l-5-5" />
              ) : (
                <path d="M18 6 6 18M6 6l12 12" />
              )}
            </svg>
            {within_budget ? "Within budget" : "Over budget"}
          </span>
        ) : null}
      </div>

      <div className="px-6 py-5">
        {sortedLines.length > 0 ? (
          <div>
            <div className="flex h-3.5 w-full overflow-hidden rounded-full">
              {sortedLines.map((line) => (
                <div
                  key={line.category}
                  className={`${line.color}`}
                  style={{ width: `${line.percent}%` }}
                  title={`${line.category}: ${formatMoney(line.amount, currency)}`}
                />
              ))}
            </div>
            <ul className="mt-5 space-y-3">
              {sortedLines.map((line) => (
                <li key={line.category} className="flex items-center justify-between gap-4">
                  <div className="flex min-w-0 items-center gap-2.5">
                    <span className={`h-2.5 w-2.5 shrink-0 rounded-sm ${line.color}`} aria-hidden="true" />
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-900">{line.category}</p>
                      <p className="truncate text-xs text-slate-500">{line.basis}</p>
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-sm font-bold text-slate-900">
                      {formatMoney(line.amount, currency)}
                    </p>
                    <p className="text-xs text-slate-400">{line.percent.toFixed(0)}%</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-slate-900 px-5 py-4 text-white">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Estimated Total
            </p>
            <p className="mt-1 font-display text-2xl font-semibold">
              {formatMoney(analysis.total_cost, currency)}
            </p>
          </div>
          {analysis.user_budget !== null && analysis.user_budget !== undefined ? (
            <div className="rounded-xl bg-slate-100 px-5 py-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Your Budget
              </p>
              <p className="mt-1 font-display text-2xl font-semibold text-slate-900">
                {formatMoney(analysis.user_budget, currency)}
              </p>
            </div>
          ) : null}
          {analysis.user_budget !== null && analysis.user_budget !== undefined ? (
            <div
              className={`rounded-xl px-5 py-4 ${
                within_budget ? "bg-teal-50" : "bg-red-50"
              }`}
            >
              <p
                className={`text-xs font-medium uppercase tracking-wide ${
                  within_budget ? "text-teal-700" : "text-red-700"
                }`}
              >
                {within_budget ? "Remaining" : "Shortfall"}
              </p>
              <p
                className={`mt-1 font-display text-2xl font-semibold ${
                  within_budget ? "text-teal-800" : "text-red-800"
                }`}
              >
                {analysis.remaining_budget !== null
                  ? formatMoney(Math.abs(analysis.remaining_budget), currency)
                  : "—"}
              </p>
            </div>
          ) : null}
        </div>

        {analysis.suggestions.length > 0 ? (
          <div className="mt-5 rounded-xl border border-teal-100 bg-teal-50/60 px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
              Ways to stay on budget
            </p>
            <ul className="mt-2 space-y-1.5">
              {analysis.suggestions.map((suggestion) => (
                <li key={suggestion} className="flex gap-2 text-sm text-slate-700">
                  <span className="text-teal-600" aria-hidden="true">→</span>
                  {suggestion}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <p className="mt-4 text-xs text-slate-400">
          Estimates use fixed daily rates and a fixed currency conversion
          (prototype). Actual costs will vary.
        </p>
      </div>
    </div>
  );
}
