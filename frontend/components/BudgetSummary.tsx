import { formatMoney } from "@/lib/money";
import type { BudgetAnalysis } from "@/types/trip";

interface BudgetSummaryProps {
  analysis: BudgetAnalysis;
  currency: string;
}

export function BudgetSummary({ analysis, currency }: BudgetSummaryProps) {
  const { within_budget } = analysis;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Budget Analysis</h3>
          {within_budget === null ? (
            <p className="mt-1 text-sm text-slate-500">
              No user budget was provided&mdash;showing an estimated total only.
            </p>
          ) : null}
        </div>

        {within_budget !== null ? (
          <span
            className={`inline-flex items-center gap-1.5 self-start rounded-full px-3 py-1 text-xs font-semibold ${
              within_budget
                ? "bg-emerald-50 text-emerald-700"
                : "bg-red-50 text-red-700"
            }`}
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: "currentColor" }}
              aria-hidden="true"
            />
            {within_budget ? "Within budget" : "Over budget"}
          </span>
        ) : null}
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-x-4 gap-y-3 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs font-medium text-slate-500">Accommodation</dt>
          <dd className="font-semibold text-slate-900">
            {formatMoney(analysis.accommodation, currency)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Transportation</dt>
          <dd className="font-semibold text-slate-900">
            {formatMoney(analysis.transportation, currency)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Food</dt>
          <dd className="font-semibold text-slate-900">
            {formatMoney(analysis.food, currency)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Activities</dt>
          <dd className="font-semibold text-slate-900">
            {formatMoney(analysis.activities, currency)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Miscellaneous</dt>
          <dd className="font-semibold text-slate-900">
            {formatMoney(analysis.miscellaneous, currency)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Estimated Total</dt>
          <dd className="font-semibold text-slate-900">
            {formatMoney(analysis.total_cost, currency)}
          </dd>
        </div>
      </dl>

      {analysis.user_budget !== null && analysis.user_budget !== undefined ? (
        <div className="mt-4 flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3 text-sm">
          <span className="text-slate-600">Your Budget</span>
          <span className="font-semibold text-slate-900">
            {formatMoney(analysis.user_budget, currency)}
          </span>
        </div>
      ) : null}
      {analysis.remaining_budget !== null &&
      analysis.remaining_budget !== undefined &&
      typeof analysis.remaining_budget === "number" &&
      within_budget !== null ? (
        <p className="mt-2 text-sm font-medium text-slate-700">
          {within_budget
            ? `You would have ${formatMoney(analysis.remaining_budget, currency)} to spare.`
            : `You need ${formatMoney(Math.abs(analysis.remaining_budget), currency)} more than your budget.`}
        </p>
      ) : null}

      {analysis.suggestions.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-medium text-slate-500">Ways to stay on budget</p>
          <ul className="mt-2 space-y-1.5">
            {analysis.suggestions.map((suggestion) => (
              <li
                key={suggestion}
                className="flex gap-2 text-sm text-slate-700"
              >
                <span className="text-emerald-600" aria-hidden="true">
                  &rarr;
                </span>
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-4 border-t border-slate-100 pt-3">
        <p className="text-xs text-slate-400">
          Estimates use fixed daily rates and a fixed currency conversion. Actual
          costs will vary.
        </p>
      </div>
    </div>
  );
}