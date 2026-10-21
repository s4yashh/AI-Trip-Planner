"use client";
import { type FormEvent, useState } from "react";
import { AirportInput } from "@/components/flights/AirportInput";
import { airportByCode, airportLabel, resolveAirport } from "@/lib/airports";
import { addDays } from "@/lib/booking-links";
import { CABINS, type Cabin, type FlightErrors, type FlightSearch, skyscannerUrl, validateFlightSearch } from "@/lib/flight-links";

export interface FlightDefaults { from?: string; to?: string; depart?: string; returnDate?: string; adults?: number }

function localToday() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}

/** Show a known code as "City (CODE)" so prefilled values look like picked ones. */
function initialText(value?: string) {
  if (!value) return "";
  const code = resolveAirport(value);
  const airport = code ? airportByCode(code) : undefined;
  return airport ? airportLabel(airport) : value;
}

function readableDate(date: string) {
  return new Date(`${date}T12:00:00`).toLocaleDateString(undefined, {weekday: "short", day: "numeric", month: "short"});
}

const input = "w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-slate-800 aria-[invalid=true]:border-red-400";

export function FlightsClient({defaults}: {defaults: FlightDefaults}) {
  const today = localToday();
  const [fromText, setFromText] = useState(initialText(defaults.from));
  const [toText, setToText] = useState(initialText(defaults.to));
  const [depart, setDepart] = useState(defaults.depart ?? addDays(today, 14));
  const [roundTrip, setRoundTrip] = useState(defaults.returnDate !== undefined || !defaults.depart);
  const [returnDate, setReturnDate] = useState(defaults.returnDate ?? addDays(defaults.depart ?? addDays(today, 14), 4));
  const [adults, setAdults] = useState(defaults.adults ?? 1);
  const [cabin, setCabin] = useState<Cabin>("economy");
  const [directOnly, setDirectOnly] = useState(false);
  const [errors, setErrors] = useState<FlightErrors>({});
  const [ready, setReady] = useState<FlightSearch | null>(null);

  const clear = (key: keyof FlightErrors) => { setErrors(previous => ({...previous, [key]: undefined})); setReady(null); };

  function swap() {
    setFromText(toText); setToText(fromText); setErrors({}); setReady(null);
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const search: FlightSearch = {from: resolveAirport(fromText) ?? fromText.trim().toUpperCase(),
      to: resolveAirport(toText) ?? toText.trim().toUpperCase(), depart, returnDate: roundTrip ? returnDate : null,
      adults, cabin, directOnly};
    if (!fromText.trim()) search.from = "";
    if (!toText.trim()) search.to = "";
    const found = validateFlightSearch(search, today);
    setErrors(found);
    if (Object.keys(found).length) { setReady(null); return; }
    setReady(search);
    window.open(skyscannerUrl(search), "_blank", "noopener,noreferrer");
  }

  const describe = (key: keyof FlightErrors, id: string) => errors[key] ? {"aria-invalid": true, "aria-describedby": `${id}-error`} : {};
  const name = (code: string) => airportByCode(code)?.city ?? code;

  return <div className="space-y-8">
    <header><p className="eyebrow">Getting there</p><h1 className="mt-2 font-display text-4xl tracking-tight">Flights</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Enter your route and dates, and we’ll open Skyscanner with everything filled in. Skyscanner compares airlines and travel sites and lets you sort by Best, Cheapest, and Fastest.</p></header>

    <section className="panel">
      <form className="grid gap-5" noValidate onSubmit={submit}>
        <div role="radiogroup" aria-label="Trip type" className="flex w-fit rounded-lg bg-[#f0f2ea] p-1 text-sm">
          {[["Round trip", true], ["One-way", false]].map(([label, value]) => <button key={String(label)} type="button" role="radio" aria-checked={roundTrip === value}
            onClick={() => { setRoundTrip(value as boolean); clear("returnDate"); }}
            className={`rounded-md px-4 py-1.5 font-medium ${roundTrip === value ? "bg-white text-[#173f3b] shadow-sm" : "text-slate-600"}`}>{label}</button>)}
        </div>

        <div className="grid items-start gap-4 md:grid-cols-[1fr_auto_1fr]">
          <AirportInput id="flight-from" label="From" value={fromText} placeholder="City or airport, e.g. Delhi" error={errors.from}
            onChange={text => { setFromText(text); clear("from"); }}/>
          <button type="button" onClick={swap} aria-label="Swap origin and destination"
            className="mx-auto mt-0 grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 md:mt-7">
            <svg viewBox="0 0 24 24" className="h-4 w-4 rotate-90 md:rotate-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M7 7h13l-4-4M17 17H4l4 4"/></svg>
          </button>
          <AirportInput id="flight-to" label="To" value={toText} placeholder="City or airport, e.g. Goa" error={errors.to}
            onChange={text => { setToText(text); clear("to"); }}/>
        </div>

        <div className="grid items-start gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="grid content-start gap-1.5 text-sm font-medium text-slate-700"><label htmlFor="flight-depart">Departure</label>
            <input id="flight-depart" type="date" min={today} className={input} value={depart} {...describe("depart", "flight-depart")}
              onChange={event => { setDepart(event.target.value); clear("depart"); }}/>
            {errors.depart && <p id="flight-depart-error" className="text-xs font-normal text-red-700">{errors.depart}</p>}</div>
          <div className="grid content-start gap-1.5 text-sm font-medium text-slate-700"><label htmlFor="flight-return">Return</label>
            <input id="flight-return" type="date" min={depart || today} className={`${input} disabled:bg-slate-50 disabled:text-slate-400`} disabled={!roundTrip}
              value={roundTrip ? returnDate : ""} {...describe("returnDate", "flight-return")}
              onChange={event => { setReturnDate(event.target.value); clear("returnDate"); }}/>
            {errors.returnDate ? <p id="flight-return-error" className="text-xs font-normal text-red-700">{errors.returnDate}</p>
              : !roundTrip && <p className="text-xs font-normal text-slate-500">One-way trip</p>}</div>
          <div className="grid content-start gap-1.5 text-sm font-medium text-slate-700"><label htmlFor="flight-adults">Passengers</label>
            <input id="flight-adults" type="number" inputMode="numeric" min={1} max={9} className={input} value={adults || ""} {...describe("adults", "flight-adults")}
              onChange={event => { setAdults(Number(event.target.value)); clear("adults"); }}/>
            {errors.adults ? <p id="flight-adults-error" className="text-xs font-normal text-red-700">{errors.adults}</p>
              : <p className="text-xs font-normal text-slate-500">Adults. Add children on Skyscanner.</p>}</div>
          <div className="grid content-start gap-1.5 text-sm font-medium text-slate-700"><label htmlFor="flight-cabin">Cabin</label>
            <select id="flight-cabin" className={input} value={cabin} onChange={event => { setCabin(event.target.value as Cabin); setReady(null); }}>
              {CABINS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></div>
        </div>

        <label className="flex w-fit items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" className="h-4 w-4 accent-[#173f3b]" checked={directOnly} onChange={event => { setDirectOnly(event.target.checked); setReady(null); }}/>
          Prefer direct flights
        </label>

        <button className="primary-btn w-full sm:w-fit">Search flights on Skyscanner<span aria-hidden="true">↗</span></button>
      </form>
    </section>

    {ready ? <section className="panel" aria-live="polite">
      <p className="eyebrow">Your search</p>
      <h2 className="mt-2 font-display text-2xl">{name(ready.from)} ({ready.from}) → {name(ready.to)} ({ready.to})</h2>
      <p className="mt-2 text-sm text-slate-600">{readableDate(ready.depart)}{ready.returnDate ? ` – ${readableDate(ready.returnDate)}` : " · one-way"} · {ready.adults} passenger{ready.adults === 1 ? "" : "s"} · {CABINS.find(option => option.value === ready.cabin)?.label}{ready.directOnly ? " · direct preferred" : ""}</p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl bg-[#eef5ef] p-4"><p className="text-sm font-semibold text-[#173f3b]">Cheapest</p><p className="mt-1 text-xs leading-5 text-slate-600">Open Skyscanner and choose the <strong>Cheapest</strong> tab to sort by lowest live fare.</p></div>
        <div className="rounded-xl bg-[#f3efe4] p-4"><p className="text-sm font-semibold text-[#6b5530]">Best (fastest / fewest stops)</p><p className="mt-1 text-xs leading-5 text-slate-600">The <strong>Best</strong> and <strong>Fastest</strong> tabs balance price, duration, and stops.</p></div>
      </div>
      <a className="primary-btn mt-5" href={skyscannerUrl(ready)} target="_blank" rel="noopener noreferrer">Open Skyscanner again<span aria-hidden="true">↗</span></a>
      <p className="mt-4 text-xs leading-5 text-slate-500">Skyscanner should have opened in a new tab. If your browser blocked it, use the button above. We don’t show fares here because no flight-price API is available to this app. Every price you see on Skyscanner is live from airlines and travel sites.</p>
    </section> : <div className="panel text-center"><p className="font-display text-xl">Where are you flying?</p>
      <p className="empty-note">Start typing a city or airport. Pick from the suggestions, or type any 3-letter airport code (like DEL or GOI).</p></div>}
  </div>;
}
