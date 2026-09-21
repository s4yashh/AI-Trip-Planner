"use client";

import { INTEREST_OPTIONS, type Interest } from "@/types/trip";

interface InterestSelectorProps {
  selected: Interest[];
  onChange: (selected: Interest[]) => void;
  error?: string;
}

const DOT_COLORS: Record<string, string> = {
  History: "#92400e",
  Architecture: "#1e40af",
  Culture: "#7c3aed",
  Nature: "#047857",
  Food: "#b91c1c",
  Shopping: "#be185d",
  Adventure: "#c2410c",
  Nightlife: "#0f172a",
};

export function InterestSelector({
  selected,
  onChange,
  error,
}: InterestSelectorProps) {
  function toggle(interest: Interest) {
    if (selected.includes(interest)) {
      onChange(selected.filter((item) => item !== interest));
    } else {
      onChange([...selected, interest]);
    }
  }

  return (
    <div>
      <span className="mb-2 block text-sm font-semibold text-slate-700">
        Interests
      </span>
      <div className="flex flex-wrap gap-2">
        {INTEREST_OPTIONS.map((interest) => {
          const active = selected.includes(interest);
          return (
            <button
              key={interest}
              type="button"
              aria-pressed={active}
              onClick={() => toggle(interest)}
              className={`flex items-center gap-2 rounded-full border px-3.5 py-2 text-sm font-medium transition-all ${
                active
                  ? "border-emerald-600 bg-emerald-600 text-white shadow-md shadow-emerald-600/25"
                  : "border-slate-200 bg-white text-slate-700 hover:-translate-y-0.5 hover:border-emerald-500 hover:text-emerald-700 hover:shadow"
              }`}
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{
                  backgroundColor: active ? "#ffffff" : DOT_COLORS[interest],
                }}
                aria-hidden="true"
              />
              {interest}
              {active ? (
                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              ) : null}
            </button>
          );
        })}
      </div>
      {error ? (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}