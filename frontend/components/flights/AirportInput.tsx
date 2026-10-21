"use client";
import { type KeyboardEvent, useId, useState } from "react";
import { type Airport, airportLabel, searchAirports } from "@/lib/airports";

export function AirportInput({id, label, value, onChange, error, placeholder}: {
  id: string; label: string; value: string; onChange: (text: string) => void; error?: string; placeholder: string;
}) {
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const matches = open ? searchAirports(value) : [];

  function choose(airport: Airport) {
    onChange(airportLabel(airport));
    setOpen(false);
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!matches.length) return;
    if (event.key === "ArrowDown") { event.preventDefault(); setActive(index => (index + 1) % matches.length); }
    else if (event.key === "ArrowUp") { event.preventDefault(); setActive(index => (index - 1 + matches.length) % matches.length); }
    else if (event.key === "Enter") { event.preventDefault(); choose(matches[active]); }
    else if (event.key === "Escape") setOpen(false);
  }

  return <div className="relative grid content-start gap-1.5 text-sm font-medium text-slate-700">
    <label htmlFor={id}>{label}</label>
    <input id={id} role="combobox" autoComplete="off" spellCheck={false} placeholder={placeholder} value={value}
      aria-expanded={matches.length > 0} aria-controls={listId} aria-autocomplete="list"
      aria-activedescendant={matches.length ? `${listId}-${active}` : undefined}
      aria-invalid={error ? true : undefined} aria-describedby={error ? `${id}-error` : undefined}
      className="w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 aria-[invalid=true]:border-red-400"
      onChange={event => { onChange(event.target.value); setOpen(true); setActive(0); }}
      onFocus={() => setOpen(true)} onBlur={() => setOpen(false)} onKeyDown={onKeyDown}/>
    {matches.length > 0 && <ul id={listId} role="listbox" className="absolute top-full z-30 mt-1 max-h-72 w-full overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
      {matches.map((airport, index) => <li key={airport.code} id={`${listId}-${index}`} role="option" aria-selected={index === active}
        className={`flex cursor-pointer items-baseline gap-3 px-3 py-2 ${index === active ? "bg-[#eff4ef]" : ""}`}
        onMouseDown={event => { event.preventDefault(); choose(airport); }} onMouseEnter={() => setActive(index)}>
        <span className="w-10 shrink-0 font-mono text-xs font-bold text-[#173f3b]">{airport.code}</span>
        <span className="min-w-0"><span className="block text-sm text-slate-800">{airport.city}, {airport.country}</span>
          <span className="block truncate text-xs font-normal text-slate-500">{airport.name}</span></span>
      </li>)}
    </ul>}
    {error && <p id={`${id}-error`} className="text-xs font-normal text-red-700">{error}</p>}
  </div>;
}
