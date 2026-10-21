"use client";
import { useEffect, useState } from "react";
import { HotelCard } from "@/components/hotels/HotelCard";
import { bookingSearchUrl, nightsBetween, type StayDetails } from "@/lib/booking-links";
import { fetchHotelSuggestions } from "@/lib/hotels-api";
import type { HotelSuggestions } from "@/types/hotels";
import type { Currency } from "@/types/live";

type Result = {key: string; data?: HotelSuggestions; error?: string};

function LoadingCards() {
  return <div className="place-grid" aria-hidden="true">{[0, 1, 2].map(index => <div key={index} className="place-card animate-pulse">
    <div className="h-4 w-24 rounded-full bg-slate-200"/><div className="mt-4 h-6 w-3/4 rounded bg-slate-200"/>
    <div className="mt-3 h-3 w-1/2 rounded bg-slate-100"/><div className="mt-6 h-8 w-1/3 rounded bg-slate-200"/>
    <div className="mt-4 flex gap-2"><div className="h-5 w-16 rounded bg-slate-100"/><div className="h-5 w-16 rounded bg-slate-100"/></div>
    <div className="mt-6 h-10 w-28 rounded-lg bg-slate-200"/>
  </div>)}</div>;
}

export function HotelSuggestionsPanel({stay, currency}: {stay: StayDetails; currency: Currency}) {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const searchKey = JSON.stringify([stay.destination, stay.checkIn, stay.checkOut, stay.adults, stay.rooms, currency]);
  const key = `${searchKey}#${attempt}`;

  useEffect(() => {
    const controller = new AbortController();
    const [destination, check_in, check_out, adults, rooms, money] = JSON.parse(searchKey);
    fetchHotelSuggestions({destination, check_in, check_out, adults, rooms, currency: money}, controller.signal)
      .then(data => setResult({key, data}))
      .catch(reason => {
        if (!controller.signal.aborted) setResult({key, error: reason instanceof Error ? reason.message : "Could not load hotel suggestions."});
      });
    return () => controller.abort();
  }, [searchKey, key]);

  const current = result?.key === key ? result : null;
  const nights = nightsBetween(stay.checkIn, stay.checkOut);
  const searchAll = <a className="secondary-btn inline-flex items-center gap-1.5" href={bookingSearchUrl(stay)} target="_blank" rel="noopener noreferrer">
    See all stays in {stay.destination} on Booking.com<span aria-hidden="true">↗</span></a>;

  return <section aria-busy={!current} aria-live="polite">
    <div className="section-intro">
      <p className="eyebrow">Where to stay</p>
      <h2>Hotels in {stay.destination}</h2>
      <p>{stay.checkIn} → {stay.checkOut} · {nights} night{nights === 1 ? "" : "s"} · {stay.adults} guest{stay.adults === 1 ? "" : "s"} · {stay.rooms} room{stay.rooms === 1 ? "" : "s"}. “Book now” opens Booking.com in a new tab with these details filled in. Nothing is booked from this app.</p>
    </div>

    {!current && <><p className="mb-4 text-sm text-slate-500" role="status">Finding hotels and estimating prices… this can take up to a minute.</p><LoadingCards/></>}

    {current?.error && <div className="error-banner" role="alert"><div><strong>Hotel suggestions are unavailable</strong><p>{current.error}</p>
      <div className="mt-3 flex flex-wrap gap-2"><button className="secondary-btn" onClick={() => setAttempt(value => value + 1)}>Try again</button>{searchAll}</div></div></div>}

    {current?.data && <>
      {current.data.resolved_location && <p className="mb-3 text-sm text-slate-600">Showing hotels near <strong>{current.data.resolved_location}</strong>. Not the right place? Add the country (e.g. “Jaipur, India”) or try a nearby larger city.</p>}
      {current.data.ai_used && <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900">
        <strong>Prices are approximate.</strong> Prices, guest ratings, and amenities marked “AI estimate” come from the AI assistant ({current.data.sources.estimates?.provider ?? "AI"}), not from a booking site. Live prices and availability are on Booking.com.</p>}
      {current.data.message && <p className="mb-4 text-xs leading-5 text-slate-500">{current.data.message}</p>}
      {current.data.suggestions.length
        ? <div className="place-grid">{current.data.suggestions.map(hotel => <HotelCard key={hotel.id} hotel={hotel} stay={stay} currency={current.data!.currency} nights={current.data!.nights}/>)}</div>
        : <div className="panel text-center"><p className="font-display text-xl">No hotel suggestions yet</p><p className="empty-note">We couldn’t find listings for this destination. You can still search every available stay on Booking.com.</p></div>}
      <div className="mt-6 flex flex-wrap items-center gap-3">{searchAll}<span className="text-[11px] text-slate-500">Hotel names: OpenStreetMap contributors (ODbL).</span></div>
    </>}
  </section>;
}
