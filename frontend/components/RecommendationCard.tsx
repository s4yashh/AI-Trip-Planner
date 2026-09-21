import { formatDuration, formatMoney } from "@/lib/money";
import type { POIRecommendation } from "@/types/trip";

interface RecommendationCardProps {
  recommendation: POIRecommendation;
  currency: string;
  rank: number;
}

const CATEGORY_TONES: Record<string, string> = {
  landmark: "bg-amber-50 text-amber-700 border-amber-200",
  museum: "bg-indigo-50 text-indigo-700 border-indigo-200",
  food: "bg-rose-50 text-rose-700 border-rose-200",
  culture: "bg-violet-50 text-violet-700 border-violet-200",
  adventure: "bg-orange-50 text-orange-700 border-orange-200",
  entertainment: "bg-sky-50 text-sky-700 border-sky-200",
  outdoors: "bg-emerald-50 text-emerald-700 border-emerald-200",
  shopping: "bg-pink-50 text-pink-700 border-pink-200",
};

function Stars({ rating }: { rating: number }) {
  return (
    <span className="flex items-center gap-1">
      <span className="flex" aria-hidden="true">
        {[1, 2, 3, 4, 5].map((i) => (
          <svg
            key={i}
            viewBox="0 0 20 20"
            className={`h-3.5 w-3.5 ${
              rating >= i - 0.25 ? "fill-amber-400" : "fill-slate-200"
            }`}
          >
            <path d="M10 1.5l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L1.6 7.6l5.8-.8L10 1.5z" />
          </svg>
        ))}
      </span>
      <span className="text-xs font-semibold text-slate-600">{rating.toFixed(1)}</span>
    </span>
  );
}

export function RecommendationCard({
  recommendation,
  currency,
  rank,
}: RecommendationCardProps) {
  const match = Math.round(recommendation.recommendation_score * 100);
  const category = recommendation.category.toLowerCase();
  const tone = CATEGORY_TONES[category] ?? "bg-slate-50 text-slate-600 border-slate-200";

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-emerald-900/10">
      <div
        className="pointer-events-none absolute -right-8 -top-10 h-28 w-28 rounded-full bg-gradient-to-br from-emerald-500/10 to-teal-500/10 transition-transform duration-500 group-hover:scale-125"
        aria-hidden="true"
      />
      {rank === 1 ? (
        <span className="absolute right-4 top-4 inline-flex items-center gap-1 rounded-full bg-amber-400/90 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-amber-950">
          <svg viewBox="0 0 24 24" className="h-3 w-3" fill="currentColor" aria-hidden="true">
            <path d="M12 2l2.9 6.3 6.9.6-5.2 4.6 1.5 6.8L12 17.2 6 20.3l1.5-6.8L2.3 8.9l6.9-.6L12 2z" />
          </svg>
          Top pick
        </span>
      ) : null}

      <div className="relative flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900">
            <span className="mr-1.5 align-middle text-xs font-black text-emerald-600">
              {String(rank).padStart(2, "0")}
            </span>
            {recommendation.name}
          </h3>
          <span className={`mt-1 inline-block rounded-full border px-2.5 py-0.5 text-[11px] font-semibold capitalize ${tone}`}>
            {recommendation.category}
          </span>
        </div>
        <span className="shrink-0 rounded-xl bg-emerald-600/10 px-2.5 py-1.5 text-right">
          <span className="block font-display text-lg font-semibold leading-none text-emerald-700">
            {match}%
          </span>
          <span className="text-[10px] font-medium uppercase tracking-wide text-emerald-700/70">
            match
          </span>
        </span>
      </div>

      <div className="relative mt-4">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400"
            style={{ width: `${match}%` }}
          />
        </div>
      </div>

      <dl className="relative mt-4 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg bg-slate-50 px-2 py-2.5">
          <dt className="text-[10px] font-medium uppercase tracking-wide text-slate-500">
            Rating
          </dt>
          <dd className="mt-1 flex justify-center">
            <Stars rating={recommendation.rating} />
          </dd>
        </div>
        <div className="rounded-lg bg-slate-50 px-2 py-2.5">
          <dt className="text-[10px] font-medium uppercase tracking-wide text-slate-500">
            Duration
          </dt>
          <dd className="mt-1 text-sm font-bold text-slate-900">
            {formatDuration(recommendation.visit_duration_hours)}
          </dd>
        </div>
        <div className="rounded-lg bg-slate-50 px-2 py-2.5">
          <dt className="text-[10px] font-medium uppercase tracking-wide text-slate-500">
            Cost
          </dt>
          <dd className="mt-1 text-sm font-bold text-slate-900">
            {formatMoney(recommendation.estimated_cost, currency)}
          </dd>
        </div>
      </dl>

      <div className="relative mt-4 flex-1 rounded-xl border border-emerald-100 bg-gradient-to-br from-emerald-50/80 to-teal-50/60 p-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-emerald-700">
          Why this was recommended
        </p>
        <p className="mt-1 text-sm leading-relaxed text-slate-700">
          {recommendation.reason}
        </p>
      </div>
    </article>
  );
}