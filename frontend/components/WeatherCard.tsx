import { SourceBadge } from "./SourceBadge";
import type { WeatherReport } from "@/types/trip";

interface WeatherCardProps {
  weather: WeatherReport;
}

export function WeatherCard({ weather }: WeatherCardProps) {
  if (weather.source === "unavailable" || weather.days.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-bold text-slate-900">Weather</h3>
          <SourceBadge source="unavailable" />
        </div>
        <p className="mt-2 text-sm text-slate-600">
          Live weather unavailable — the itinerary was planned without
          weather adjustment.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-[#e9e2d3] bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-[#eee9df] px-6 py-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Weather</h3>
          <p className="text-sm text-slate-500">{weather.message}</p>
        </div>
        <SourceBadge source={weather.source} />
      </div>
      <ul className="grid grid-cols-1 gap-3 px-6 py-5 sm:grid-cols-2 xl:grid-cols-3">
        {weather.days.map((day) => (
          <li
            key={day.day_number}
            className={`rounded-xl border px-4 py-3 ${
              day.avoid_outdoor
                ? "border-sky-200 bg-sky-50/60"
                : "border-slate-100 bg-slate-50/60"
            }`}
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-bold text-slate-900">
                Day {day.day_number}
              </p>
              <p className="text-xs text-slate-500">{day.date}</p>
            </div>
            <p className="mt-1 text-sm font-semibold text-slate-700">
              {day.condition || "—"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {day.temp_min_c !== null && day.temp_max_c !== null
                ? `${day.temp_min_c}–${day.temp_max_c}°C`
                : "Temperature n/a"}
              {day.precipitation_probability !== null
                ? ` · ${day.precipitation_probability}% rain`
                : ""}
              {day.wind_speed_kmh !== null
                ? ` · ${day.wind_speed_kmh} km/h wind`
                : ""}
            </p>
            {day.avoid_outdoor ? (
              <p className="mt-1.5 text-xs font-semibold text-sky-700">
                Outdoor visits moved off this day
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
