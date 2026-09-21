"use client";

const STEPS = [
  "Understanding your preferences",
  "Finding places that match your interests",
  "Building a day-wise itinerary",
  "Estimating the budget",
];

export function LoadingState() {
  return (
    <div className="overflow-hidden rounded-2xl border border-[#e9e2d3] bg-white shadow-sm">
      <div className="h-1.5 w-full overflow-hidden bg-slate-100">
        <div
          className="h-full w-1/3 animate-[shimmer_1.2s_ease-in-out_infinite] rounded-full bg-[#f26b4f]"
          aria-hidden="true"
        />
      </div>
      <div className="flex flex-col items-center gap-4 px-8 py-12 text-center">
        <div
          className="relative flex h-14 w-14 items-center justify-center"
          aria-hidden="true"
        >
          <div className="absolute inset-0 animate-ping rounded-full border-2 border-[#f26b4f]" />
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#17233d] text-white shadow-lg shadow-slate-900/20">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m3 11 18-7-7 18-2.5-7.5L3 11z" />
            </svg>
          </div>
        </div>

        <div>
          <p className="font-display text-xl font-semibold text-slate-900">
            Planning your trip...
          </p>
          <p className="mx-auto mt-1.5 max-w-sm text-sm text-slate-500">
            Your request is being processed by the AI planning service. This can
            take a moment.
          </p>
        </div>

        <ul className="mt-2 w-full max-w-sm space-y-2.5 text-left">
          {STEPS.map((step) => (
            <li
              key={step}
              className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-600"
            >
              <span
                className="relative flex h-2 w-2 shrink-0"
                aria-hidden="true"
              >
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#f26b4f] opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#f26b4f]" />
              </span>
              {step}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
