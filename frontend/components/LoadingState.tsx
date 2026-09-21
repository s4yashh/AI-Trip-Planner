"use client";

const STEPS = [
  "Understanding your preferences",
  "Finding places that match your interests",
  "Building a day-wise itinerary",
  "Estimating the budget",
];

export function LoadingState() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="flex flex-col items-center gap-4 text-center">
        <div
          className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600"
          aria-hidden="true"
        />
        <p className="font-semibold text-slate-900">Planning your trip...</p>
        <p className="max-w-sm text-sm text-slate-600">
          Your request is being processed by the AI planning service. This can
          take a moment.
        </p>
        <ul className="mt-2 w-full max-w-sm space-y-2 text-left">
          {STEPS.map((step) => (
            <li key={step} className="flex items-center gap-2.5 text-sm text-slate-600">
              <span className="flex h-2 w-2 shrink-0 animate-pulse rounded-full bg-emerald-500" aria-hidden="true" />
              {step}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}