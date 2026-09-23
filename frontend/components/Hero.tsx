import Link from "next/link";

export function Hero() {
  return <section className="relative overflow-hidden bg-[#173f3b] text-white">
    <div className="travel-grid absolute inset-0 opacity-30" aria-hidden="true" />
    <div className="relative mx-auto max-w-6xl px-6 py-24 sm:py-32">
      <p className="text-xs font-semibold uppercase tracking-[.2em] text-[#c3d2b6]">Your personal travel studio</p>
      <h1 className="mt-6 max-w-3xl font-display text-5xl leading-[1.1] tracking-tight sm:text-7xl">A journey that moves<br/>with <span className="text-[#e6b88f]">you.</span></h1>
      <p className="mt-7 max-w-xl text-base leading-8 text-[#c3d1c6]">Bring your itinerary, places to stay, restaurants, weather, and budget together. Plan with your preferences, and keep your journey up to date as conditions change.</p>
      <div className="mt-9 flex flex-wrap gap-4"><Link className="rounded-xl bg-[#e5b58e] px-7 py-3.5 text-sm font-semibold text-[#173f3b]" href="/plan">Open your travel studio ↗</Link><Link className="rounded-xl border border-white/20 px-7 py-3.5 text-sm" href="/about">How it works</Link></div>
    </div>
  </section>;
}
