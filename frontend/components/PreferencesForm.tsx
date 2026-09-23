"use client";
import { useState } from "react";
import { categories, type Preferences } from "@/types/live";

export function PreferencesForm({initial, busy, editing, onSave}: {
  initial: Preferences; busy: boolean; editing: boolean; onSave: (value: Preferences) => Promise<void>;
}) {
  const [value, setValue] = useState(initial);
  const [interestsText, setInterestsText] = useState(initial.interests.join(", "));
  const [dietText, setDietText] = useState(initial.dietary_preferences.join(", "));
  const set = <K extends keyof Preferences>(key: K, next: Preferences[K]) => setValue(current => ({...current, [key]: next}));
  const split = (text: string) => text.split(",").map(s => s.trim()).filter(Boolean);
  return <form className="trip-form" onSubmit={e => {e.preventDefault(); void onSave({...value, interests:split(interestsText), dietary_preferences:split(dietText)});}}>
    <label>Destination<input required maxLength={200} value={value.destination} placeholder="City or destination" onChange={e => set("destination", e.target.value)} /></label>
    <div className="field-pair">
      <label>Start date<input required type="date" value={value.start_date} onChange={e => set("start_date", e.target.value)} /></label>
      <label>Days<input required type="number" min={1} max={60} value={value.number_of_days} onChange={e => set("number_of_days", Number(e.target.value))} /></label>
    </div>
    <div className="field-pair">
      <label>Total budget<input type="number" min={0} step="0.01" value={value.budget ?? ""} placeholder="Optional" onChange={e => set("budget", e.target.value === "" ? null : Number(e.target.value))} /></label>
      <label>Currency<select value={value.currency} onChange={e => set("currency", e.target.value as Preferences["currency"])}><option>INR</option><option>USD</option></select></label>
    </div>
    <label>Interests<span className="field-hint">Separate with commas</span><input value={interestsText} placeholder="Art, history, nature…" onChange={e => setInterestsText(e.target.value)} /></label>
    <div className="field-pair">
      <label>Travelers<input required type="number" min={1} max={20} value={value.travelers} onChange={e => set("travelers", Number(e.target.value))} /></label>
      <label>Rooms<input required type="number" min={1} max={10} value={value.rooms} onChange={e => set("rooms", Number(e.target.value))} /></label>
    </div>
    <div className="field-pair">
      <label>Getting around<select value={value.transport_mode} onChange={e => set("transport_mode", e.target.value as Preferences["transport_mode"])}><option value="walking">Walking</option><option value="driving">Driving</option></select></label>
      <label>Your pace<select value={value.pace} onChange={e => set("pace", e.target.value as Preferences["pace"])}><option value="relaxed">Relaxed</option><option value="balanced">Balanced</option><option value="busy">Busy</option></select></label>
    </div>
    <label>Dietary preferences<input value={dietText} placeholder="Vegetarian, vegan…" onChange={e => setDietText(e.target.value)} /></label>
    <details className="allowances"><summary>Cost allowances <span>Optional</span></summary>
      <p>Enter total-trip amounts for everyone, in {value.currency}. These cover missing prices. Leave unknown costs blank; enter 0 only when you expect no cost.</p>
      {categories.map(category => <label key={category} className="capitalize">{category}<input type="number" min={0} step="0.01" value={value.allowances[category] ?? ""} placeholder="Unknown" onChange={e => set("allowances", {...value.allowances, [category]: e.target.value === "" ? null : Number(e.target.value)})} /></label>)}
    </details>
    <button className="primary-btn w-full" disabled={busy}>{busy ? "Working on your trip…" : editing ? "Save preferences & replan" : "Create my trip"}<span aria-hidden="true">↗</span></button>
    <p className="form-footnote">Your trip stays on this computer. Recommendations depend on available live information.</p>
  </form>;
}
