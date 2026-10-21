"use client";
import { type FormEvent, useState } from "react";
import { HotelSuggestionsPanel } from "@/components/hotels/HotelSuggestionsPanel";
import { addDays, type StayDetails, type StayErrors, validateStay } from "@/lib/booking-links";
import type { Currency } from "@/types/live";

export interface HotelSearchDefaults {
  destination?: string; checkIn?: string; checkOut?: string; adults?: number; rooms?: number; currency?: Currency;
}

function localToday() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}

const input = "w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 aria-[invalid=true]:border-red-400";

function Field({label, error, id, children}: {label: string; error?: string; id: string; children: React.ReactNode}) {
  return <div className="grid content-start gap-1.5 text-sm font-medium text-slate-700"><label htmlFor={id}>{label}</label>{children}
    {error && <p id={`${id}-error`} className="text-xs font-normal text-red-700">{error}</p>}</div>;
}

export function HotelsClient({defaults}: {defaults: HotelSearchDefaults}) {
  const today = localToday();
  const [form, setForm] = useState<StayDetails>({
    destination: defaults.destination ?? "",
    checkIn: defaults.checkIn ?? addDays(today, 7),
    checkOut: defaults.checkOut ?? addDays(defaults.checkIn ?? addDays(today, 7), 2),
    adults: defaults.adults ?? 2,
    rooms: defaults.rooms ?? 1,
  });
  const [currency, setCurrency] = useState<Currency>(defaults.currency ?? "INR");
  const [errors, setErrors] = useState<StayErrors>({});
  const ready = !!defaults.destination && !Object.keys(validateStay(form, today)).length;
  const [search, setSearch] = useState<{stay: StayDetails; currency: Currency} | null>(ready ? {stay: form, currency} : null);

  function update<K extends keyof StayDetails>(key: K, value: StayDetails[K]) {
    setForm(previous => ({...previous, [key]: value}));
    setErrors(previous => ({...previous, [key]: undefined}));
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const stay = {...form, destination: form.destination.trim()};
    const found = validateStay(stay, today);
    setErrors(found);
    if (Object.keys(found).length) return;
    setSearch({stay, currency});
    const params = new URLSearchParams({destination: stay.destination, check_in: stay.checkIn, check_out: stay.checkOut,
      adults: String(stay.adults), rooms: String(stay.rooms), currency});
    window.history.replaceState({}, "", `/hotels?${params}`);
  }

  const described = (key: keyof StayErrors, id: string) => errors[key] ? {"aria-invalid": true, "aria-describedby": `${id}-error`} : {};

  return <div className="space-y-8">
    <header><p className="eyebrow">Find a place to stay</p><h1 className="mt-2 font-display text-4xl tracking-tight">Hotels</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Get 3–5 hotel picks labelled Cheapest, Best rated, and Best value, then book on Booking.com with your dates already filled in.</p></header>

    <section className="panel">
      <form className="grid gap-4" noValidate onSubmit={submit}>
        <Field label="Destination" id="hotel-destination" error={errors.destination}>
          <input id="hotel-destination" className={input} maxLength={200} value={form.destination} placeholder="e.g. Jaipur, India"
            onChange={event => update("destination", event.target.value)} {...described("destination", "hotel-destination")}/>
        </Field>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Field label="Check-in" id="hotel-check-in" error={errors.checkIn}>
            <input id="hotel-check-in" type="date" className={input} min={today} value={form.checkIn}
              onChange={event => update("checkIn", event.target.value)} {...described("checkIn", "hotel-check-in")}/>
          </Field>
          <Field label="Check-out" id="hotel-check-out" error={errors.checkOut}>
            <input id="hotel-check-out" type="date" className={input} min={form.checkIn ? addDays(form.checkIn, 1) : today} value={form.checkOut}
              onChange={event => update("checkOut", event.target.value)} {...described("checkOut", "hotel-check-out")}/>
          </Field>
          <Field label="Guests" id="hotel-adults" error={errors.adults}>
            <input id="hotel-adults" type="number" inputMode="numeric" min={1} max={30} className={input} value={form.adults || ""}
              onChange={event => update("adults", Number(event.target.value))} {...described("adults", "hotel-adults")}/>
          </Field>
          <Field label="Rooms" id="hotel-rooms" error={errors.rooms}>
            <input id="hotel-rooms" type="number" inputMode="numeric" min={1} max={10} className={input} value={form.rooms || ""}
              onChange={event => update("rooms", Number(event.target.value))} {...described("rooms", "hotel-rooms")}/>
          </Field>
          <Field label="Currency" id="hotel-currency">
            <select id="hotel-currency" className={input} value={currency} onChange={event => setCurrency(event.target.value as Currency)}>
              <option value="INR">INR (₹)</option><option value="USD">USD ($)</option></select>
          </Field>
        </div>
        <button className="primary-btn w-full sm:w-fit">Find hotels<span aria-hidden="true">↗</span></button>
      </form>
    </section>

    {search ? <HotelSuggestionsPanel stay={search.stay} currency={search.currency}/>
      : <div className="panel text-center"><p className="font-display text-xl">Where are you headed?</p>
        <p className="empty-note">Enter a destination and your dates above. Tip: if you’ve planned a trip, open it and use its Hotels tab, where everything is filled in for you.</p></div>}
  </div>;
}
