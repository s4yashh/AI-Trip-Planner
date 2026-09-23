"use client";
import { useCallback, useEffect, useState } from "react";
import { LLMSetup } from "@/components/LLMSetup";
import { PreferencesForm } from "@/components/PreferencesForm";
import { BudgetPanel, HistoryPanel, Itinerary, Overview, PlacesPanel } from "@/components/TripDetails";
import { emptyPreferences, money, request, RequestError } from "@/lib/live-api";
import type { Activity, Capabilities, Preferences, Revision, Trip, TripSummary } from "@/types/live";

const tabs = ["Overview", "Itinerary", "Budget", "Places", "Assistant", "History"] as const;
type Tab = typeof tabs[number];

export function TripDashboard() {
  const [trips, setTrips] = useState<TripSummary[]>([]);
  const [trip, setTrip] = useState<Trip | null>(null);
  const [draft, setDraft] = useState<Preferences>(emptyPreferences);
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("Overview");
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [message, setMessage] = useState("");
  const [draftReply, setDraftReply] = useState("");

  const loadList = useCallback(async () => {setTrips(await request<TripSummary[]>("/trips"));}, []);
  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const [saved, status] = await Promise.all([request<TripSummary[]>("/trips"), request<Capabilities>("/capabilities")]);
        if (!mounted) return;
        setTrips(saved); setCapabilities(status);
        const id = new URLSearchParams(window.location.search).get("trip");
        if (id) {
          const selected = await request<Trip>(`/trips/${encodeURIComponent(id)}`);
          if (mounted) setTrip(selected);
        }
      } catch (reason) {if (mounted) setError(reason instanceof Error ? reason.message : "Could not load trips.");}
      finally {if (mounted) setLoading(false);}
    }
    void load();
    return () => {mounted = false;};
  }, []);

  const tripId = trip?.id;
  useEffect(() => {
    if (!tripId || busy) return;
    let cancelled = false;
    async function poll() {
      if (document.visibilityState !== "visible") return;
      try {
        const current = await request<Trip>(`/trips/${tripId}`);
        if (!cancelled) setTrip(previous => previous?.id === current.id && current.version >= previous.version ? current : previous);
      } catch (reason) {if (!cancelled) setError(reason instanceof Error ? reason.message : "Refresh failed.");}
    }
    const timer = window.setInterval(() => void poll(), 30_000);
    document.addEventListener("visibilitychange", poll);
    return () => {cancelled = true; clearInterval(timer); document.removeEventListener("visibilitychange", poll);};
  }, [tripId, busy]);

  const version = trip?.version;
  useEffect(() => {
    if (tab !== "History" || !tripId) return;
    let cancelled = false;
    request<Revision[]>(`/trips/${tripId}/revisions`).then(value => {if (!cancelled) setRevisions(value);})
      .catch(reason => {if (!cancelled) setError(reason.message);});
    return () => {cancelled = true;};
  }, [tab, tripId, version]);

  function selectUrl(id?: string) { window.history.replaceState({}, "", id ? `/plan?trip=${encodeURIComponent(id)}` : "/plan"); }
  async function openTrip(id: string) {
    setBusy(true); setError("");
    try {setTrip(await request<Trip>(`/trips/${id}`)); selectUrl(id); setTab("Overview");}
    catch (reason) {setError(reason instanceof Error ? reason.message : "Could not open trip.");}
    finally {setBusy(false);}
  }
  async function mutate(path: string, method: string, body: unknown): Promise<Trip | null> {
    setBusy(true); setError("");
    try {
      const result = await request<Trip>(path, method, body);
      setTrip(result); selectUrl(result.id);
      await loadList();
      return result;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update trip.");
      if (reason instanceof RequestError && reason.status === 409 && trip) {
        const latest = await request<Trip>(`/trips/${trip.id}`).catch(() => null);
        if (latest) setTrip(latest);
      }
      return null;
    } finally {setBusy(false);}
  }
  function newTrip() {setTrip(null); setDraft(emptyPreferences()); setDraftReply(""); setError(""); setTab("Overview"); selectUrl();}
  async function savePreferences(preferences: Preferences) {
    const result = await mutate(trip ? `/trips/${trip.id}` : "/trips", trip ? "PATCH" : "POST", trip ? {version: trip.version, preferences} : preferences);
    if (result) setTab("Itinerary");
  }
  function updateActivity(activity: Activity, changes: Partial<Activity>) {
    if (trip) void mutate(`/trips/${trip.id}/activities/${encodeURIComponent(activity.id)}`, "PATCH", {version:trip.version, ...changes});
  }
  async function sendMessage() {
    if (!message.trim()) return;
    if (trip) {
      const result = await mutate(`/trips/${trip.id}/chat`, "POST", {version:trip.version, message});
      if (result) setMessage("");
      return;
    }
    setBusy(true); setError("");
    try {
      const result = await request<{explanation:string; preference_changes:Partial<Preferences>}>("/chat/draft", "POST", {message, preferences:draft.destination.trim() ? draft : null});
      setDraft(current => ({...current, ...result.preference_changes})); setDraftReply(result.explanation); setMessage("");
    } catch (reason) {setError(reason instanceof Error ? reason.message : "Assistant unavailable.");}
    finally {setBusy(false);}
  }

  const assistant = <section className="panel assistant-panel"><div className="section-intro"><p className="eyebrow">Your travel assistant</p><h2>Talk through your next adventure.</h2><p>{capabilities?.llm.message ?? "Connect a local model or Gemini to plan conversationally. You can always use the trip form."}</p></div>
    <div className="chat-messages" aria-live="polite">{trip?.conversation.map((entry,index) => <div key={index} className={`chat-message chat-${entry.role}`}><span>{entry.role === "user" ? "You" : "Assistant"}</span><p>{entry.content}</p></div>)}{!trip && draftReply && <div className="chat-message chat-assistant"><span>Assistant</span><p>{draftReply}</p><small>Review the extracted preferences in the form, then create your trip.</small></div>}</div>
    <form className="trip-form" onSubmit={e => {e.preventDefault(); void sendMessage();}}><label htmlFor="assistant-message">Your message<textarea id="assistant-message" required maxLength={4000} rows={4} placeholder={trip ? "Ask about your plan or describe a preference change…" : "Describe where, when, and how you would like to travel…"} value={message} onChange={e => setMessage(e.target.value)}/></label><button disabled={busy || !message.trim()} className="primary-btn">{busy ? "Thinking…" : `Send to ${capabilities?.llm.provider === "gemini" ? "Gemini" : "assistant"}`}<span aria-hidden="true">↗</span></button></form><p className="form-footnote">Conversation can update your preferences and itinerary. Use trip details for monetary changes.</p>
    <LLMSetup status={capabilities?.llm}/>
  </section>;

  return <main className="planner-shell">
    <div className="planner-heading"><div><p className="eyebrow">THE TRAVEL STUDIO</p><h1>Good plans. Better journeys.</h1><p>A personal itinerary that keeps up with your trip.</p></div><span className="local-pill"><span/>Saved on your computer</span></div>
    {error && <div className="error-banner" role="alert"><div><strong>Something needs attention</strong><p>{error}</p></div><button onClick={() => setError("")} aria-label="Dismiss error">×</button></div>}
    <div className="planner-grid"><aside className="planner-sidebar">
      <section className="panel saved-panel"><div className="section-heading"><h2>Your journeys</h2><button className="text-button" disabled={busy} onClick={newTrip}>+ New trip</button></div>
        {loading ? <p className="empty-note">Loading saved trips…</p> : !trips.length ? <p className="empty-note">A fresh start. Your saved trips will appear here.</p> : <div className="saved-list">{trips.map(saved => <button disabled={busy} key={saved.id} onClick={() => void openTrip(saved.id)} className={trip?.id === saved.id ? "saved-trip active" : "saved-trip"}><span className="saved-icon" aria-hidden="true">↗</span><span><strong>{saved.destination}</strong><small>{saved.start_date} · {saved.number_of_days} days</small></span><span className={`trip-dot ${saved.valid ? "valid" : ""}`} title={saved.valid ? "Validated" : "Needs review"}/></button>)}</div>}
      </section>
      <section className="panel preferences-panel"><div className="preferences-heading"><p className="eyebrow">{trip ? "MAKE IT YOURS" : "START SOMEWHERE NEW"}</p><h2>Trip details</h2></div>
        <PreferencesForm key={trip ? `${trip.id}-${JSON.stringify(trip.preferences)}` : JSON.stringify(draft)} initial={trip?.preferences ?? draft} busy={busy} editing={!!trip} onSave={savePreferences}/>
      </section>
    </aside>
    <div className="planner-content" aria-busy={busy}>
      {!trip ? <><section className="welcome-card"><div className="welcome-art" aria-hidden="true"><svg viewBox="0 0 360 180"><path d="M25 160 Q80 40 130 100 T250 60 T335 20" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="5 8"/><circle cx="130" cy="100" r="7"/><circle cx="250" cy="60" r="7"/><path d="m315 20 32-8-13 30-5-15Z"/></svg><span>EXPLORE AT YOUR OWN PACE</span></div><p className="eyebrow">A WORLD OF POSSIBILITIES</p><h2>Where will curiosity<br/>take you next?</h2><p>Choose a destination, set your pace, and bring the details together. Your plan begins with you.</p><div className="welcome-chips"><span>Personal itineraries</span><span>Live conditions</span><span>Thoughtful budgets</span></div></section>{assistant}</> : <>
        <section className="trip-hero"><div><p className="eyebrow">YOUR NEXT CHAPTER</p><h2>{trip.preferences.destination}</h2><p>{trip.preferences.start_date} · {trip.preferences.number_of_days} days · {trip.preferences.travelers} traveler(s)</p></div><span className={`plan-status ${trip.plan.valid ? "" : "needs-review"}`}>{trip.plan.valid ? "Schedule validated" : "Needs review"}</span></section>
        <div className="trip-stats"><div><span>Planned experiences</span><strong>{trip.plan.activities.length}</strong></div><div><span>{trip.plan.budget.complete ? "Projected total" : "Known costs · incomplete"}</span><strong>{money(trip.plan.budget.complete ? trip.plan.budget.total : trip.plan.budget.known_total,trip.preferences.currency)}</strong></div><div><span>Recorded spending</span><strong>{money(trip.plan.budget.spent,trip.preferences.currency)}</strong></div></div>
        <div className="monitor-bar"><div><strong><span className={`monitor-dot ${trip.monitoring ? "enabled" : ""}`}/>{trip.monitoring ? "Automatic updates on" : "Automatic updates paused"}</strong><small>{trip.last_checked ? `Last checked ${new Date(trip.last_checked).toLocaleString()}` : "Not checked yet"}</small></div><div className="flex flex-wrap gap-2"><button className="secondary-btn" disabled={busy} onClick={() => void mutate(`/trips/${trip.id}`,"PATCH",{version:trip.version, monitoring:!trip.monitoring})}>{trip.monitoring ? "Pause updates" : "Resume updates"}</button><button className="secondary-btn" disabled={busy} onClick={() => void mutate(`/trips/${trip.id}/refresh`,"POST",{version:trip.version})}>{busy ? "Updating…" : "Refresh now"}</button></div></div>
        {!!trip.plan.conflicts.length && <div className="conflict-banner" role="status"><strong>Your plan needs a review</strong><ul>{trip.plan.conflicts.map((warning,i) => <li key={i}>{warning}</li>)}</ul></div>}
        {!!trip.plan.warnings.length && <details className="trip-notes"><summary>{trip.plan.warnings.length} planning note{trip.plan.warnings.length === 1 ? "" : "s"}</summary><ul>{trip.plan.warnings.map((warning,i) => <li key={i}>{warning}</li>)}</ul></details>}
        <nav className="trip-tabs" aria-label="Trip sections">{tabs.map(label => <button key={label} aria-current={tab===label ? "page" : undefined} className={tab===label ? "active" : ""} onClick={() => setTab(label)}>{label}</button>)}</nav>
        <div className="tab-content">
          {tab === "Overview" && <Overview trip={trip}/>}
          {tab === "Itinerary" && <Itinerary trip={trip} busy={busy} onActivity={updateActivity}/>}
          {tab === "Budget" && <BudgetPanel trip={trip} busy={busy} onExpense={async (category,amount,description) => !!await mutate(`/trips/${trip.id}/expenses`,"POST",{version:trip.version,expense:{category,amount,description}})}/>}
          {tab === "Places" && <PlacesPanel trip={trip}/>}
          {tab === "Assistant" && assistant}
          {tab === "History" && <HistoryPanel revisions={revisions}/>}
        </div>
      </>}
    </div></div>
  </main>;
}
