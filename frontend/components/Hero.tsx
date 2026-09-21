import Link from "next/link";

export function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-4 pb-16 pt-16 text-center sm:px-6 sm:pt-24">
      <p className="mx-auto mb-4 inline-block rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
        Multi-Agent AI Trip Planner
      </p>
      <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
        Plan Your Perfect Trip <span className="text-emerald-600">with AI</span>
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-base text-slate-600 sm:text-lg">
        Create a personalized travel itinerary using multiple AI agents working
        together &mdash; a recommendation agent finds places you will love, an
        itinerary agent schedules your days, and a budget agent keeps your trip
        on track.
      </p>
      <div className="mt-8">
        <Link
          href="/plan"
          className="inline-block rounded-lg bg-emerald-600 px-6 py-3 text-base font-semibold text-white transition-colors hover:bg-emerald-700"
        >
          Start Planning
        </Link>
      </div>

      <div className="mx-auto mt-14 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { step: "01", title: "Recommend", text: "POIs ranked against your interests." },
          { step: "02", title: "Schedule", text: "A day-wise, time-bounded itinerary." },
          { step: "03", title: "Budget", text: "Transparent cost estimate and tips." },
        ].map((item) => (
          <div
            key={item.step}
            className="rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm"
          >
            <p className="text-xs font-semibold text-emerald-600">{item.step}</p>
            <h3 className="mt-1 text-sm font-semibold text-slate-900">{item.title}</h3>
            <p className="mt-1 text-sm text-slate-600">{item.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}