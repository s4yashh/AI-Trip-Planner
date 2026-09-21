import { formatDuration, formatMoney } from "@/lib/money";
import type { Itinerary, ItineraryDay } from "@/types/trip";

interface ItineraryCardProps {
  itinerary: Itinerary;
  currency: string;
}

function DayTimeline({ day, currency }: { day: ItineraryDay; currency: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h4 className="mb-4 text-sm font-bold uppercase tracking-wide text-emerald-700">
        Day {day.day_number}
      </h4>
      <ol className="relative space-y-0 border-l border-slate-200 pl-5">
        {day.items.map((item, index) => (
          <li key={`${item.poi_id}-${index}`} className="relative pb-6">
            <span
              className="absolute -left-[27px] top-1 h-2.5 w-2.5 rounded-full border-2 border-emerald-500 bg-white"
              aria-hidden="true"
            />
            <div className="flex flex-col gap-1">
              <p className="text-sm font-semibold text-slate-900">
                {item.start_time} &ndash; {item.end_time}
              </p>
              <p className="text-sm text-slate-700">{item.name}</p>
              <p className="text-xs text-slate-500">
                {formatDuration(item.duration_hours)} &middot;{" "}
                {formatMoney(item.estimated_cost, currency)}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function ItineraryCard({ itinerary, currency }: ItineraryCardProps) {
  if (itinerary.days.length === 0) {
    return (
      <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600 shadow-sm">
        No itinerary was generated for these preferences.
      </p>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {itinerary.days.map((day) => (
          <DayTimeline key={day.day_number} day={day} currency={currency} />
        ))}
      </div>
      {itinerary.skipped_poi_ids.length > 0 ? (
        <p className="mt-4 text-sm text-amber-700">
          Skipped because no daily slot fits: {itinerary.skipped_poi_ids.join(", ")}
        </p>
      ) : null}
    </div>
  );
}