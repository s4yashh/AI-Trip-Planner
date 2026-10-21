import Link from "next/link";

export function Hero() {
  return <section className="relative overflow-hidden bg-[#173f3b] text-white">
    <div className="travel-grid absolute inset-0 opacity-30" aria-hidden="true" />
    <div className="relative mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
      <p className="text-xs font-semibold uppercase tracking-[.2em] text-[#c3d2b6]">Your personal travel studio</p>
      <h1 className="mt-6 max-w-3xl font-display text-4xl leading-[1.1] tracking-tight sm:text-6xl">A journey that moves<br/>with <span className="text-[#e6b88f]">you.</span></h1>
      <p className="mt-7 max-w-xl text-base leading-8 text-[#c3d1c6]">Bring your itinerary, places to stay, restaurants, weather, and budget together. Plan with your preferences, and keep your journey up to date as conditions change.</p>
      <div className="mt-9 flex flex-wrap gap-3"><Link className="hero-cta" href="/plan">Plan a trip ↗</Link><Link className="hero-cta-secondary" href="/group-plan">Plan with a group</Link></div>
    </div>
  </section>;
}
