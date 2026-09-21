"use client";

import { INTEREST_OPTIONS, type Interest } from "@/types/trip";

interface InterestSelectorProps {
  selected: Interest[];
  onChange: (selected: Interest[]) => void;
  error?: string;
}

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
      <span className="mb-2 block text-sm font-medium text-slate-700">
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
              className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
                active
                  ? "border-emerald-600 bg-emerald-600 text-white"
                  : "border-slate-300 bg-white text-slate-700 hover:border-emerald-500 hover:text-emerald-700"
              }`}
            >
              {interest}
            </button>
          );
        })}
      </div>
      {error ? (
        <p className="mt-1.5 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}