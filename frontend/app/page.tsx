import Link from "next/link";
import { Hero } from "@/components/Hero";
import { Icon, type IconName } from "@/components/ui/Icon";

const tools: [IconName, string, string, string][] = [
  ["map", "/plan", "Plan a trip", "A day-by-day itinerary from live places, weather, and your interests. It updates as conditions change."],
  ["users", "/group-plan", "Plan with a group", "Everyone adds their budget, interests, and pace. Get one fair plan, with conflicts resolved day by day."],
  ["plane", "/flights", "Find flights", "Enter your route and dates, and open a pre-filled Skyscanner search to compare live fares."],
  ["bed", "/hotels", "Find hotels", "See picks labelled Cheapest, Best rated, and Best value, then book on Booking.com."],
];

const steps = [
  ["1", "Tell us about the trip", "Destination, dates, interests, and pace. Add a budget if you have one."],
  ["2", "Review your plan", "See the itinerary, weather, places, and costs. Unknown prices stay clearly marked."],
  ["3", "Book and go", "Open hotels and flights with your details filled in. The plan keeps up while you travel."],
];

export default function Home() {
  return <main>
    <Hero/>
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <p className="eyebrow">Everything in one place</p>
      <h2 className="mt-3 font-display text-3xl tracking-tight sm:text-4xl">What would you like to do?</h2>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {tools.map(([icon, href, title, detail]) => <Link key={href} href={href} className="panel tool-card">
          <span className="tool-icon"><Icon name={icon} className="h-6 w-6"/></span>
          <h3 className="mt-5">{title}</h3>
          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{detail}</p>
          <span className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--brand)]">Get started <Icon name="arrow" className="h-4 w-4"/></span>
        </Link>)}
      </div>

      <h2 className="mt-20 font-display text-3xl tracking-tight sm:text-4xl">How it works</h2>
      <ol className="mt-8 grid gap-4 md:grid-cols-3">
        {steps.map(([number, title, detail]) => <li key={number} className="panel flex gap-4">
          <span className="step-number">{number}</span>
          <div><h3>{title}</h3><p className="mt-2 text-sm leading-6 text-[var(--muted)]">{detail}</p></div>
        </li>)}
      </ol>
      <p className="mt-10 text-sm leading-7 text-[var(--muted)]">Your trips are saved on this computer. What’s available depends on the destination and data provider, and unknown prices stay unknown. This planner doesn’t make bookings or payments; booking links open the provider’s own site.</p>
    </section>
  </main>;
}
