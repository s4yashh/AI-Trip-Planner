import { formatDuration, formatMoney } from "@/lib/money";
import type { POIRecommendation } from "@/types/trip";

interface RecommendationCardProps {
  recommendation: POIRecommendation;
  currency: string;
}

export function RecommendationCard({
  recommendation,
  currency,
}: RecommendationCardProps) {
  const match = Math.round(recommendation.recommendation_score * 100);

  return (
    <article className="flex flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            {recommendation.name}
          </h3>
          <p className="text-sm capitalize text-slate-500">
            {recommendation.category}
          </p>
        </div>
        <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
          {match}% match
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-xs font-medium text-slate-500">Rating</dt>
          <dd className="font-semibold text-slate-900">{recommendation.rating}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Visit Duration</dt>
          <dd className="font-semibold text-slate-900">
            {formatDuration(recommendation.visit_duration_hours)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Estimated Cost</dt>
          <dd className="font-semibold text-slate-900">
            {formatMoney(recommendation.estimated_cost, currency)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-slate-500">Recommendation Match</dt>
          <dd className="font-semibold text-slate-900">{match}%</dd>
        </div>
      </dl>

      <div className="mt-4 rounded-lg bg-slate-50 p-3">
        <p className="text-xs font-medium text-slate-500">Why this was recommended</p>
        <p className="mt-0.5 text-sm text-slate-700">{recommendation.reason}</p>
      </div>
    </article>
  );
}