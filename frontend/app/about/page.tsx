const agents = [
  ["Recommendations", "Ranks live attractions against your interests using content similarity."],
  ["Weather", "Uses available forecasts to prefer indoor activities when rain or wind affects your plans."],
  ["Itinerary", "Schedules visits, respects known opening hours and travel gaps, and preserves locked or completed activities."],
  ["Accommodation", "Finds lodging listings and, when configured, dated hotel offers with provider prices."],
  ["Transport & traffic", "Provides routes and traffic-aware driving times when available. Geographic estimates are clearly identified."],
  ["Restaurants", "Recommends nearby restaurants and highlights source-provided dietary information."],
  ["Budget", "Combines hotel quotes, your total-trip allowances, and recorded expenses without counting spending twice."],
  ["Emergency information", "Lists nearby medical and police facilities with source-provided contacts and map links."],
  ["Validation & coordination", "Checks proposed updates before applying them. Unresolved conflicts retain the previous itinerary."],
];
export default function AboutPage() {
  return <main className="mx-auto max-w-5xl px-6 py-16"><p className="eyebrow">Working together, for your journey</p><h1 className="mt-3 font-display text-5xl tracking-tight">One trip. Many thoughtful agents.</h1><p className="mt-6 max-w-2xl text-sm leading-7 text-slate-500">Specialist agents coordinate live information and your preferences. A local language model supports conversation, while scheduling and validation keep changes within defined constraints.</p><div className="mt-10 grid gap-5 sm:grid-cols-2">{agents.map(([title,detail]) => <article key={title} className="panel"><h2>{title}</h2><p className="mt-3 text-sm leading-7 text-slate-500">{detail}</p></article>)}</div><section className="panel mt-8"><h2>What to expect</h2><p className="mt-4 text-sm leading-7 text-slate-500">Automatic checks run every 15 minutes for trips within the forecast window while the backend remains open. The interface refreshes every 30 seconds while visible. Providers can be unavailable, and opening hours do not establish ticket availability. You can inspect sources, pause monitoring, and review every applied itinerary change.</p><p className="mt-4 text-sm leading-7 text-slate-500">Hotel prices and traffic need configured providers. Conversations need an already running local model. Structured planning remains available without a model. This local application does not book travel, take payments, or dispatch emergency assistance.</p></section></main>;
}
