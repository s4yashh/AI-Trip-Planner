import { formatMoney } from "@/lib/money";
import type { TripSummary } from "@/types/trip";

interface TripOverviewProps {
  summary: TripSummary;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur-sm">
      <dt className="text-xs font-medium text-slate-300">{label}</dt>
      <dd className="mt-1 text-lg font-bold text-white">{value}</dd>
    </div>
  );
}

export function TripOverview({ summary }: TripOverviewProps) {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-[#17233d] p-7 text-white shadow-xl shadow-slate-900/15 sm:p-9">
      <div className="travel-grid absolute inset-0 opacity-40" aria-hidden="true" />
      <div className="pointer-events-none absolute -right-10 -top-16 h-64 w-64 rounded-full bg-[#f26b4f]/20 blur-3xl" aria-hidden="true" />

      <div className="relative">
        <p className="text-xs font-semibold uppercase tracking-widest text-[#ffb08e]">
          Your personalized plan
        </p>
        <h2 className="mt-1 font-display text-3xl font-semibold capitalize tracking-tight sm:text-4xl">
          {summary.destination}
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-300">
          {summary.message}
        </p>

        <dl className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat
            label="Days"
            value={`${summary.number_of_days} ${summary.number_of_days === 1 ? "day" : "days"}`}
          />
          <Stat
            label="Budget"
            value={
              summary.budget === null
                ? "Not set"
                : `${formatMoney(summary.budget, summary.currency)}`
            }
          />
          <Stat
            label="Estimated Total"
            value={
              summary.total_estimated_cost === null
                ? "—"
                : `${formatMoney(summary.total_estimated_cost, summary.currency)}`
            }
          />
          <Stat
            label="Places Found"
            value={`${summary.recommended_count}`}
          />
        </dl>

        <div className="mt-5 flex flex-wrap gap-2">
          {summary.interests.map((interest) => (
            <span
              key={interest}
              className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold capitalize text-slate-100"
            >
              {interest}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
