"use client";
import { useState } from "react";
import { categories, type Activity, type Category, type Place, type Revision, type Source, type Trip } from "@/types/live";
import { money, safeWebsite, sourceLabel } from "@/lib/live-api";

export function SourceTag({source}: {source: Source}) {
  const label = sourceLabel(source);
  return <span className={`source-tag source-${label}`} title={`${source.provider}${source.retrieved_at ? ` · Retrieved ${new Date(source.retrieved_at).toLocaleString()}` : ""}${source.message ? ` · ${source.message}` : ""}`}>{label.replaceAll("_", " ")}</span>;
}

export function PlaceCards({places, empty}: {places: Place[]; empty: string}) {
  if (!places.length) return <p className="empty-note">{empty}</p>;
  return <div className="place-grid">{places.map(place => {
    const website = safeWebsite(place.website);
    return <article className="place-card" key={place.id}>
      <div className="flex justify-between gap-2"><p className="eyebrow">{place.kind.replaceAll("_", " ")}</p><SourceTag source={place.source} /></div>
      <h3>{place.name}</h3><p>{place.reason || "Listed in OpenStreetMap"}</p>
      <p className="place-hours">{place.opening_hours ? `Listed hours: ${place.opening_hours}` : "Opening hours unknown"}</p>
      {place.phone && <p>Contact: <a href={`tel:${place.phone.replace(/[^+\d]/g, "")}`}>{place.phone}</a></p>}
      <div className="place-links"><a href={`https://www.openstreetmap.org/?mlat=${place.latitude}&mlon=${place.longitude}#map=16/${place.latitude}/${place.longitude}`} target="_blank" rel="noreferrer">View on map ↗</a>{website && <a href={website} target="_blank" rel="noreferrer">Website ↗</a>}</div>
    </article>;
  })}</div>;
}

export function Itinerary({trip, busy, onActivity}: {trip: Trip; busy: boolean; onActivity: (activity: Activity, changes: Partial<Activity>) => void}) {
  const days = Array.from({length: trip.preferences.number_of_days}, (_, i) => {
    const date = new Date(trip.preferences.start_date+"T12:00:00Z"); date.setUTCDate(date.getUTCDate()+i); return date.toISOString().slice(0,10);
  });
  return <div><div className="section-intro"><h2>A little structure. Room to explore.</h2><p>Times are local to {trip.plan.timezone}. Lock activities to keep their schedule during updates.</p></div>
    {days.map((day, index) => <section className="day-card" key={day}>
      <header><span className="day-number">{String(index+1).padStart(2,"0")}</span><div><p className="eyebrow">Day {index+1}</p><h3>{new Date(day+"T12:00:00").toLocaleDateString(undefined, {weekday:"long", month:"short", day:"numeric"})}</h3></div></header>
      {!trip.plan.activities.some(a => a.date === day) && <p className="empty-note">No activities scheduled for this day. Adjust your preferences or refresh when more information is available.</p>}
      {trip.plan.activities.filter(a => a.date === day).map(activity => {
        const route = trip.plan.routes.find(r => r.from_id === activity.place.id);
        return <div className={`activity ${activity.completed ? "activity-completed" : ""}`} key={activity.id}>
          <div className="activity-time"><strong>{activity.start_time}</strong><span>{activity.end_time}</span></div>
          <div className="activity-body"><div className="flex items-center gap-2"><p className="eyebrow">{activity.place.kind}</p><SourceTag source={activity.place.source}/></div><h4>{activity.place.name}</h4><p>{activity.place.reason}</p>
            <p className="text-xs text-slate-500">{activity.duration_minutes} min planned visit · Entry price unknown · {activity.place.opening_hours ? `Listed hours: ${activity.place.opening_hours}` : "Opening hours unknown"}</p>
            <div className="activity-actions">
              <button aria-pressed={activity.locked} disabled={busy} onClick={() => onActivity(activity, {locked: !activity.locked})}>{activity.locked ? "Unlock" : "Lock time"}</button>
              <button aria-pressed={activity.completed} disabled={busy} onClick={() => onActivity(activity, {completed: !activity.completed})}>{activity.completed ? "Mark incomplete" : "Mark completed"}</button>
              <button aria-pressed={activity.committed} disabled={busy} onClick={() => onActivity(activity, {committed: !activity.committed})}>{activity.committed ? "Remove commitment" : "Mark committed"}</button>
              <a href={`https://www.openstreetmap.org/?mlat=${activity.place.latitude}&mlon=${activity.place.longitude}`} target="_blank" rel="noreferrer">Map ↗</a>
            </div>
            {route && <div className="route-line"><span>↳ {route.minutes ?? "Unknown"} min to next stop · {route.distance_km ?? "Unknown"} km</span><SourceTag source={route.source} />
              {route.traffic_delay_minutes != null && <span>Traffic delay: {route.traffic_delay_minutes} min</span>}
              <p>{route.source.message}</p>
              {!!route.instructions.length && <details><summary>Directions</summary><ol>{route.instructions.map((step, i) => <li key={i}>{step}</li>)}</ol></details>}
            </div>}
          </div>
        </div>;
      })}
    </section>)}
  </div>;
}

export function BudgetPanel({trip, busy, onExpense}: {trip: Trip; busy: boolean; onExpense: (category: Category, amount: number, description: string) => Promise<boolean>}) {
  const [category, setCategory] = useState<Category>("food");
  const [amount, setAmount] = useState(""); const [description, setDescription] = useState("");
  const budget = trip.plan.budget, currency = trip.preferences.currency;
  return <><div className="section-intro"><h2>Keep the journey in balance.</h2><p>Projected costs use the greater of each total-trip allowance or recorded spending. Expenses are not counted twice.</p></div>
    <div className="budget-total"><p>{budget.complete ? "Projected trip total" : "Known costs so far"}</p><strong>{money(budget.complete ? budget.total : budget.known_total, currency)}</strong><span>{budget.complete ? budget.within_budget === false ? "Over budget — review your costs" : "Includes quotes and your allowances" : "Incomplete — add missing allowances in trip details"}</span></div>
    <div className="table-scroll"><table className="budget-table"><thead><tr><th>Category</th><th>Planned</th><th>Spent</th><th>Projected</th></tr></thead><tbody>{budget.lines.map(line => <tr key={line.category}><td><strong className="capitalize">{line.category}</strong><small>{line.basis}</small></td><td>{money(line.planned,currency)}</td><td>{money(line.spent,currency)}</td><td>{money(line.projected,currency)}</td></tr>)}</tbody></table></div>
    {budget.conversion_note && <p className="empty-note">{budget.conversion_note}</p>}
    <section className="panel mt-6"><h3>Record an expense</h3><form className="expense-form trip-form" onSubmit={async e => {e.preventDefault(); if (await onExpense(category, Number(amount), description)) {setAmount(""); setDescription("");}}}>
      <label>Category<select value={category} onChange={e => setCategory(e.target.value as Category)}>{categories.map(c => <option key={c}>{c}</option>)}</select></label>
      <label>Amount ({currency})<input required min={0} step="0.01" type="number" value={amount} onChange={e => setAmount(e.target.value)} /></label>
      <label className="expense-description">Description<input required maxLength={300} value={description} onChange={e => setDescription(e.target.value)} /></label>
      <button disabled={busy} className="primary-btn">Add expense</button>
    </form><div className="expense-list">{trip.expenses.map(expense => <div key={expense.id}><span>{expense.description}<small>{expense.category}</small></span><strong>{money(expense.amount,currency)}</strong></div>)}</div></section>
  </>;
}

export function Overview({trip}: {trip: Trip}) {
  return <><div className="section-intro"><h2>Your trip, connected.</h2><p>Weather, places, and costs come together here. Updates run while the backend is open.</p></div>
    <section className="panel"><div className="section-heading"><h3>The forecast</h3>{trip.plan.sources.weather && <SourceTag source={trip.plan.sources.weather} />}</div>
      {!trip.plan.weather.length ? <p className="empty-note">{trip.plan.sources.weather?.message || "Weather unavailable for these dates."}</p> : <div className="weather-grid">{trip.plan.weather.map(day => <div className={`weather-day ${day.avoid_outdoor ? "weather-caution" : ""}`} key={day.date}><p>{new Date(day.date+"T12:00:00").toLocaleDateString(undefined,{month:"short",day:"numeric"})}</p><span aria-hidden="true">{day.avoid_outdoor ? "☂" : "☀"}</span><strong>{day.temperature_max ?? "—"}° / {day.temperature_min ?? "—"}°</strong><small>Rain {day.rain_probability ?? "unknown"}%</small><small>{day.avoid_outdoor ? "Indoor plans preferred" : "Check conditions before leaving"}</small></div>)}</div>}
    </section>
    <section className="panel mt-5"><h3>Planning agents</h3><div className="agent-grid">{Object.entries(trip.plan.agents).map(([name,status]) => <div key={name}><span className="capitalize">{name.replaceAll("_"," ")}</span><strong className={status === "complete" || status === "passed" ? "text-teal-700" : "text-slate-500"}>{status}</strong></div>)}</div></section>
    <section className="panel mt-5"><h3>Information sources</h3><div className="source-list">{Object.entries(trip.plan.sources).map(([key,source]) => <div key={key}><div><strong>{source.provider}</strong><SourceTag source={source}/></div><p>{source.message || `${key.replaceAll("_"," ")} information`}</p>{source.retrieved_at && <small>Retrieved {new Date(source.retrieved_at).toLocaleString()}</small>}</div>)}</div></section>
  </>;
}

export function PlacesPanel({trip}: {trip: Trip}) {
  return <><div className="section-intro"><h2>Stay, eat, and explore.</h2><p>Listings describe places. Prices, ticket inventory, and dietary suitability are unknown unless explicitly supplied.</p></div>
    <h3 className="collection-title">Accommodation offers</h3>
    {trip.plan.hotels.length ? <div className="place-grid">{trip.plan.hotels.map(h => <article className="place-card" key={h.id}><SourceTag source={h.source}/><h3>{h.name}</h3><strong>{money(h.amount,h.currency)}</strong><p>{h.check_in} → {h.check_out} · {h.rooms} room(s), full stay</p><p>Offer snapshot; no reservation has been made.</p></article>)}</div> : <p className="empty-note">{trip.plan.sources.accommodation?.message || "No hotel offers found for these dates."}</p>}
    <h3 className="collection-title">Nearby lodging</h3><PlaceCards places={trip.plan.lodging} empty="No lodging listings available."/>
    <h3 className="collection-title">Restaurants & cafés</h3><PlaceCards places={trip.plan.restaurants} empty="No restaurant listings available."/>
    <h3 className="collection-title">Recommended places</h3><PlaceCards places={trip.plan.places} empty="No attractions found. Check the destination and provider status."/>
    <h3 className="collection-title">Help nearby</h3><p className="mb-4 text-sm text-slate-600">Facility information and source-provided contacts. This app cannot call or dispatch emergency services.</p><PlaceCards places={trip.plan.emergency} empty="Emergency facility information is unavailable. Consult local official services."/>
  </>;
}

export function HistoryPanel({revisions}: {revisions: Revision[]}) {
  return <><div className="section-intro"><h2>Every change, explained.</h2><p>Your previous plans remain available in the trip history.</p></div>{revisions.map(revision => <details className="revision" key={revision.version}><summary><span className="revision-number">v{revision.version}</span><span>{revision.reason}<small>{new Date(revision.created_at).toLocaleString()}</small></span></summary><div className="revision-comparison">{[{label:"Before",trip:revision.before},{label:"After",trip:revision.after}].map(side => <div key={side.label}><h4>{side.label}</h4>{side.trip?.plan.activities.map(a => <p key={a.id}>{a.date} · {a.start_time} · {a.place.name}</p>) ?? <p>New trip</p>}<p>Known total: {side.trip ? money(side.trip.plan.budget.known_total,side.trip.preferences.currency) : "—"}</p></div>)}</div></details>)}</>;
}
