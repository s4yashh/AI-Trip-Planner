import { formatMoney } from "@/lib/money";
import type { TripSummary } from "@/types/trip";

interface TripOverviewProps {
  summary: TripSummary;
}

export function TripOverview({ summary }: TripOverviewProps) {
  return (
    <div className="rounded-xl bg-slate-900 p-6 text-white shadow-sm">
      <h2 className="text-2xl font-bold capitalize">{summary.destination}</h2>
      <p className="mt-1 text-sm text-slate-300">{summary.message}</p>

      <dl className="mt-5 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-xs font-medium text-slate-400">Days</dt>
          <dd className="mt-1 text-lg font-semibold">{summary.number_of_days}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-400">Budget</dt>
          <dd className="mt-1 text-lg font-semibold">
            {summary.budget === null
              ? "Not set"
              : formatMoney(summary.budget, summary.currency)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-400">Interests</dt>
          <dd className="mt-1 flex flex-wrap gap-1">
            {summary.interests.map((interest) => (
              <span
                key={interest}
                className="rounded-full bg-emerald-600/20 px-2 py-0.5 text-xs font-medium text-emerald-300"
              >
                {interest}
              </span>
            ))}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-400">Estimated Total</dt>
          <dd className="mt-1 text-lg font-semibold">
            {summary.total_estimated_cost === null
              ? "—"
              : formatMoney(summary.total_estimated_cost, summary.currency)}
          </dd>
        </div>
      </dl>
    </div>
  );
}