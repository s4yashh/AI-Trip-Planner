import Link from "next/link";

const PIPELINE = [
  { label: "Recommend", detail: "Places ranked against your interests" },
  { label: "Schedule", detail: "Day-wise, time-bounded itinerary" },
  { label: "Budget", detail: "Transparent estimate and tips" },
];

const STATS = [
  { value: "3", label: "AI agents" },
  { value: "9", label: "destinations" },
  { value: "48", label: "places" },
  { value: "8", label: "interests" },
];

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-emerald-950 via-emerald-900 to-teal-900 text-white">
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="absolute -left-24 -top-24 h-96 w-96 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="absolute -right-16 top-32 h-80 w-80 rounded-full bg-teal-400/20 blur-3xl" />
        <div className="absolute bottom-0 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-amber-400/10 blur-3xl" />
        <svg className="absolute inset-0 h-full w-full opacity-[0.07]" aria-hidden="true">
          <defs>
            <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
              <path d="M48 0H0v48" fill="none" stroke="white" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 pb-20 pt-16 sm:px-6 lg:grid-cols-2 lg:pt-24">
        <div>
          <p className="animate-fade-up inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3.5 py-1.5 text-xs font-semibold uppercase tracking-widest text-emerald-200">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" aria-hidden="true" />
            Multi-Agent AI Trip Planner
          </p>

          <h1 className="animate-fade-up-delay-1 mt-6 font-display text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            Plan your perfect trip,{" "}
            <span className="bg-gradient-to-r from-emerald-300 via-teal-200 to-amber-200 bg-clip-text text-transparent">
              crafted by AI
            </span>
          </h1>

          <p className="animate-fade-up-delay-1 mt-5 max-w-xl text-lg leading-relaxed text-emerald-100/80">
            Three specialised agents work together to recommend places you will
            love, schedule every day of your trip, and keep the whole journey
            inside your budget.
          </p>

          <div className="animate-fade-up-delay-2 mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="/plan"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 font-semibold text-emerald-900 shadow-xl shadow-black/20 transition-transform hover:-translate-y-0.5"
            >
              Start Planning
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </Link>
            <Link
              href="/about"
              className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-6 py-3 font-semibold text-white backdrop-blur transition-colors hover:bg-white/10"
            >
              How it works
            </Link>
          </div>

          <dl className="animate-fade-up-delay-2 mt-10 grid max-w-md grid-cols-4 gap-4 border-t border-white/10 pt-6">
            {STATS.map((stat) => (
              <div key={stat.label}>
                <dt className="order-2 text-xs font-medium text-emerald-100/70">
                  {stat.label}
                </dt>
                <dd className="font-display text-2xl font-semibold text-white">
                  {stat.value}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="animate-fade-up-delay-2 hidden lg:block">
          <div className="relative ml-auto max-w-md">
            <div
              className="absolute -inset-3 rounded-3xl bg-gradient-to-br from-emerald-400/30 to-teal-400/20 blur-2xl"
              aria-hidden="true"
            />
            <div className="relative rounded-3xl border border-white/15 bg-white/10 p-7 shadow-2xl backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-white">Your trip, layer by layer</p>
                <span className="rounded-full bg-emerald-400/20 px-2.5 py-1 text-xs font-semibold text-emerald-200">
                  Live
                </span>
              </div>
              <div className="mt-6 space-y-5">
                {PIPELINE.map((step, index) => (
                  <div key={step.label} className="flex items-start gap-3.5">
                    <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-400 text-sm font-bold text-emerald-950">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-semibold text-white">{step.label}</p>
                      <p className="text-sm text-emerald-100/70">{step.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-7 flex items-center gap-2.5 rounded-xl bg-white/10 px-4 py-3 text-sm text-emerald-50">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-400 text-emerald-950" aria-hidden="true">
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                </span>
                Every result is computed by real agents — nothing is staged.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}