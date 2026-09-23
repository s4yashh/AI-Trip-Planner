import { SourceBadge } from "./SourceBadge";
import type { RestaurantList } from "@/types/trip";

interface RestaurantCardProps {
  restaurants: RestaurantList;
}

function priceLabel(level: number): string {
  return "₹".repeat(Math.min(Math.max(level, 1), 3));
}

export function RestaurantCard({ restaurants }: RestaurantCardProps) {
  if (restaurants.source === "unavailable" || restaurants.results.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-bold text-slate-900">Restaurants</h3>
          <SourceBadge source="unavailable" />
        </div>
        <p className="mt-2 text-sm text-slate-600">
          Live restaurant data unavailable and no local options exist for
          this destination.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-[#e9e2d3] bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-[#eee9df] px-6 py-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Restaurants</h3>
          <p className="text-sm text-slate-500">{restaurants.message}</p>
        </div>
        <SourceBadge source={restaurants.source} />
      </div>
      <ul className="grid grid-cols-1 gap-4 px-6 py-5 md:grid-cols-2">
        {restaurants.results.map((item) => (
          <li
            key={item.restaurant_id}
            className="rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-bold text-slate-900">{item.name}</p>
                <p className="text-xs capitalize text-slate-500">
                  {item.cuisine || "various cuisines"}
                  {item.distance_km !== null
                    ? ` · ${item.distance_km} km away`
                    : ""}
                </p>
              </div>
              <span className="shrink-0 rounded-lg bg-teal-50 px-2 py-1 text-right">
                <span className="block font-display text-base font-semibold leading-none text-[#0f766e]">
                  {item.restaurant_score.toFixed(2)}
                </span>
                <span className="text-[10px] font-medium uppercase tracking-wide text-teal-700/70">
                  score
                </span>
              </span>
            </div>
            <div className="mt-2 flex items-center gap-3 text-xs text-slate-600">
              <span className="font-semibold">
                ★ {item.rating > 0 ? item.rating.toFixed(1) : "unrated"}
              </span>
              <span className="font-semibold text-slate-500">
                {priceLabel(item.price_level)}
              </span>
              <SourceBadge source={item.source} />
            </div>
            {item.reason ? (
              <p className="mt-1.5 text-xs leading-relaxed text-slate-600">
                {item.reason}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
