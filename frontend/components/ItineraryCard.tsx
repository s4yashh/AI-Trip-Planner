import { formatDuration, formatMoney } from "@/lib/money";
import type { Itinerary, ItineraryDay } from "@/types/trip";

interface ItineraryCardProps {
  itinerary: Itinerary;
  currency: string;
}

function DayTimeline({ day, currency }: { day: ItineraryDay; currency: string }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-[#e9e2d3] bg-white shadow-sm transition-shadow hover:shadow-lg">
      <div className="flex items-center gap-3 border-b border-[#e9e2d3] bg-[#fdfbf7] px-5 py-3.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#17233d] font-display text-base font-semibold text-white">
          {day.day_number}
        </span>
        <div>
          <p className="text-sm font-bold text-slate-900">Day {day.day_number}</p>
          <p className="text-xs text-slate-500">
            {day.items.length} {day.items.length === 1 ? "place" : "places"} scheduled
          </p>
        </div>
      </div>

      <ol className="px-5 py-4">
        {day.items.length === 0 ? (
          <li className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-500">
            Free day — nothing scheduled. The plan still covers all{" "}
            requested days.
          </li>
        ) : null}
        {day.items.map((item, index) => {
          const last = index === day.items.length - 1;
          return (
            <li key={`${item.poi_id}-${index}`} className="relative flex gap-4 pb-5">
              {!last ? (
                <span
                  className="absolute left-[13px] top-8 bottom-0 w-px bg-slate-200"
                  aria-hidden="true"
                />
              ) : null}
              <span
                className="relative mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-[#0f766e] bg-white"
                aria-hidden="true"
              >
                <span className="h-2 w-2 rounded-full bg-[#0f766e]" />
              </span>

              <div className="flex-1">
                <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                  <p className="text-sm font-bold text-slate-900">{item.name}</p>
                  <p className="inline-flex items-center gap-1.5 rounded-full bg-slate-900 px-2.5 py-0.5 text-xs font-semibold text-white">
                    <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
                      <circle cx="12" cy="12" r="9" />
                      <path d="M12 7v5l3 2" />
                    </svg>
                    {item.start_time} – {item.end_time}
                  </p>
                </div>
                <p className="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-slate-500">
                  <span>{formatDuration(item.duration_hours)} visit</span>
                  <span className="font-semibold text-slate-700">
                    {formatMoney(item.estimated_cost, currency)}
                  </span>
                  {item.travel_minutes_to_next !== null &&
                  item.travel_minutes_to_next !== undefined ? (
                    <span className="font-medium text-slate-500">
                      +{item.travel_minutes_to_next} min travel
                      {item.travel_source === "live"
                        ? " (live)"
                        : item.travel_source === "estimate"
                          ? " (est.)"
                          : ""}
                    </span>
                  ) : null}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export function ItineraryCard({ itinerary, currency }: ItineraryCardProps) {
  if (itinerary.days.length === 0) {
    return (
      <p className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        No itinerary was generated for these preferences.
      </p>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        {itinerary.days.map((day) => (
          <DayTimeline key={day.day_number} day={day} currency={currency} />
        ))}
      </div>
      {itinerary.skipped_poi_ids.length > 0 ? (
        <p className="mt-4 flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M10.3 4.2 2.9 17a2 2 0 0 0 1.7 3h14.8a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0z" />
            <path d="M12 9v4M12 17h.01" />
          </svg>
          Skipped because no daily slot fits: {itinerary.skipped_poi_ids.join(", ")}
        </p>
      ) : null}
    </div>
  );
}
