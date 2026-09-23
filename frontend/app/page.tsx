import { Hero } from "@/components/Hero";
const steps = [
  ["01", "Make it personal", "Set your destination, interests, pace, and budget. An existing local model can help you talk through your preferences."],
  ["02", "Bring the details together", "Explore live place listings, weather forecasts, and optional hotel and traffic information, with clear sources."],
  ["03", "Let the plan adapt", "Automatic updates revisit future activities. Lock commitments, track spending, and see why each revision happened."],
];
export default function Home() {
  return <main><Hero/><section className="mx-auto max-w-6xl px-6 py-20"><p className="eyebrow">From first thought to final stop</p><h2 className="mt-3 font-display text-4xl tracking-tight">More of the journey. Less of the juggling.</h2><div className="mt-10 grid gap-6 md:grid-cols-3">{steps.map(([number,title,detail]) => <article className="panel" key={number}><p className="eyebrow">{number}</p><h3 className="mt-5">{title}</h3><p className="mt-4 text-sm leading-7 text-slate-500">{detail}</p></article>)}</div><p className="mt-10 text-sm leading-7 text-slate-500">Your trips are saved locally. Data availability varies by destination and provider; unknown prices stay unknown. The planner does not make bookings or payments.</p></section></main>;
}
