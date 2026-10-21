"use client";

import {useEffect, useState, type FormEvent} from "react";
import {groupRequest} from "@/lib/group-trip-api";
import type {GroupMember, GroupMemberPreferences, GroupTrip, GroupTripCreate} from "@/types/group-trip";

function localToday() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}

function money(value: number | null, currency: "INR" | "USD") {
  if (value === null) return "Unknown";
  return new Intl.NumberFormat("en-IN", {style: "currency", currency, maximumFractionDigits: 2}).format(value);
}

function MemberPreferencesCard({member, busy, onSave}: {
  member: GroupMember;
  busy: boolean;
  onSave: (memberId: string, preferences: GroupMemberPreferences) => Promise<void>;
}) {
  const [budget, setBudget] = useState(member.preferences?.budget?.toString() ?? "");
  const [interests, setInterests] = useState(member.preferences?.interests.join(", ") ?? "");
  const [pace, setPace] = useState<GroupMemberPreferences["pace"]>(member.preferences?.pace ?? "moderate");
  const interestsId = `interests-${member.id}`;
  const budgetId = `budget-${member.id}`;
  const paceId = `pace-${member.id}`;

  return <form className="panel space-y-4" onSubmit={event => {
    event.preventDefault();
    void onSave(member.id, {
      budget: budget.trim() ? Number(budget) : null,
      interests: interests.split(",").map(item => item.trim()).filter(Boolean),
      pace,
    });
  }}>
    <div className="flex items-center justify-between gap-3">
      <div><p className="eyebrow">MEMBER PREFERENCES</p><h3 className="mt-1 font-display text-xl">{member.name}</h3></div>
      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${member.preferences ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"}`}>
        {member.preferences ? "Saved" : "Not submitted"}
      </span>
    </div>
    <label className="grid gap-1.5 text-sm font-medium text-slate-700" htmlFor={budgetId}>
      Personal trip budget <span className="text-xs font-normal text-slate-500">Optional cap, in the group currency</span>
      <input id={budgetId} type="number" min={0} step="0.01" value={budget} onChange={event => setBudget(event.target.value)}
        className="rounded-lg border border-slate-300 bg-white px-3 py-2" placeholder="Enter budget or leave unknown"/>
    </label>
    <label className="grid gap-1.5 text-sm font-medium text-slate-700" htmlFor={interestsId}>
      Interests <span className="text-xs font-normal text-slate-500">Separate with commas; first is your top interest</span>
      <input id={interestsId} required value={interests} onChange={event => setInterests(event.target.value)}
        className="rounded-lg border border-slate-300 bg-white px-3 py-2" placeholder="Beach, food, history…"/>
    </label>
    <label className="grid gap-1.5 text-sm font-medium text-slate-700" htmlFor={paceId}>
      Preferred pace
      <select id={paceId} value={pace} onChange={event => setPace(event.target.value as GroupMemberPreferences["pace"])}
        className="rounded-lg border border-slate-300 bg-white px-3 py-2">
        <option value="relaxed">Relaxed</option><option value="moderate">Moderate</option><option value="packed">Packed</option>
      </select>
    </label>
    <button className="secondary-btn" disabled={busy || !interests.split(",").some(item => item.trim())}>
      {busy ? "Saving…" : member.preferences ? "Update preferences" : `Save ${member.name}`}
    </button>
    <p className="text-xs leading-5 text-slate-500">Members enter preferences separately in this group workspace. No account or external invite link is required.</p>
  </form>;
}

export function GroupTripClient({initialGroupId}: {initialGroupId?: string}) {
  const [group, setGroup] = useState<GroupTrip | null>(null);
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState(localToday);
  const [days, setDays] = useState(3);
  const [memberCount, setMemberCount] = useState(3);
  const [currency, setCurrency] = useState<"INR" | "USD">("INR");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(Boolean(initialGroupId));
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let active = true;
    if (!initialGroupId) return () => {active = false;};
    void groupRequest<GroupTrip>(`/${encodeURIComponent(initialGroupId)}`).then(value => {
      if (active) {
        setGroup(value);
        setDestination(value.destination);
        setStartDate(value.start_date);
        setDays(value.number_of_days);
        setMemberCount(value.member_count);
        setCurrency(value.currency);
      }
    }).catch(reason => {
      if (active) setError(reason instanceof Error ? reason.message : "Could not load this group trip.");
    }).finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [initialGroupId]);

  async function createGroup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const payload: GroupTripCreate = {destination, start_date: startDate, number_of_days: days,
        member_count: memberCount, currency};
      const saved = await groupRequest<GroupTrip>("", "POST", payload);
      setGroup(saved);
      window.history.replaceState({}, "", `/group-plan?group=${encodeURIComponent(saved.id)}`);
      setMessage("Group created. Each member can now save their own preferences.");
    } catch (reason) {setError(reason instanceof Error ? reason.message : "Could not create this group trip.");}
    finally {setBusy(false);}
  }

  async function saveMember(memberId: string, preferences: GroupMemberPreferences) {
    if (!group) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const saved = await groupRequest<GroupTrip>(`/${encodeURIComponent(group.id)}/members/${encodeURIComponent(memberId)}`,
        "PATCH", {version: group.version, preferences});
      setGroup(saved);
      setMessage("Member preferences saved.");
    } catch (reason) {setError(reason instanceof Error ? reason.message : "Could not save member preferences.");}
    finally {setBusy(false);}
  }

  async function generatePlan() {
    if (!group) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const saved = await groupRequest<GroupTrip>(`/${encodeURIComponent(group.id)}/plan`, "POST", {version: group.version});
      setGroup(saved);
      setMessage("Group itinerary generated.");
    } catch (reason) {setError(reason instanceof Error ? reason.message : "Could not generate a group itinerary.");}
    finally {setBusy(false);}
  }

  function resetGroup() {
    setGroup(null); setError(""); setMessage(""); setDestination(""); setStartDate(localToday());
    setDays(3); setMemberCount(3); setCurrency("INR");
    window.history.replaceState({}, "", "/group-plan");
  }

  if (loading) return <p className="empty-note">Loading group trip…</p>;

  const allPreferencesSaved = !!group?.members.every(member => member.preferences !== null);
  const result = group?.plan;

  return <div className="space-y-7">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="eyebrow">A PLAN FOR EVERYONE</p><h1 className="mt-2 font-display text-4xl tracking-tight">Group Trip Planning</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Balance individual interests and budgets into one explainable itinerary. Member preferences are entered separately.</p></div>
      {group && <button className="secondary-btn" disabled={busy} onClick={resetGroup}>Start another group</button>}
    </header>
    {error && <div className="error-banner" role="alert"><div><strong>Something needs attention</strong><p>{error}</p></div></div>}
    {message && <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900" role="status">{message}</p>}

    {!group ? <section className="panel max-w-2xl">
      <div className="mb-5"><p className="eyebrow">STEP 1</p><h2 className="mt-1 font-display text-2xl">Create the shared trip</h2></div>
      <form className="grid gap-4" onSubmit={event => void createGroup(event)}>
        <label className="grid gap-1.5 text-sm font-medium text-slate-700">Destination
          <input required maxLength={200} value={destination} onChange={event => setDestination(event.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2" placeholder="City or destination"/>
        </label>
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="grid gap-1.5 text-sm font-medium text-slate-700">Start date
            <input required type="date" value={startDate} onChange={event => setStartDate(event.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2"/>
          </label>
          <label className="grid gap-1.5 text-sm font-medium text-slate-700">Days
            <input required type="number" min={1} max={30} value={days} onChange={event => setDays(Number(event.target.value))}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2"/>
          </label>
          <label className="grid gap-1.5 text-sm font-medium text-slate-700">Members
            <input required type="number" min={2} max={20} value={memberCount} onChange={event => setMemberCount(Number(event.target.value))}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2"/>
          </label>
        </div>
        <label className="grid max-w-48 gap-1.5 text-sm font-medium text-slate-700">Currency
          <select value={currency} onChange={event => setCurrency(event.target.value as "INR" | "USD")}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2"><option>INR</option><option>USD</option></select>
        </label>
        <p className="text-xs leading-5 text-slate-500">Group data is stored separately from your existing single-person trips.</p>
        <button className="primary-btn w-fit" disabled={busy}>{busy ? "Creating group…" : "Create group"}<span aria-hidden="true">↗</span></button>
      </form>
    </section> : <>
      <section className="rounded-2xl bg-[#173f3b] p-6 text-white sm:p-8">
        <p className="eyebrow text-emerald-100">SHARED TRIP</p><h2 className="mt-2 font-display text-3xl">{group.destination}</h2>
        <p className="mt-2 text-sm text-emerald-50">{group.start_date} · {group.number_of_days} days · {group.member_count} members</p>
        <p className="mt-3 text-xs text-emerald-100">Group reference: {group.id}</p>
      </section>

      <section className="space-y-4">
        <div><p className="eyebrow">STEP 2</p><h2 className="mt-1 font-display text-2xl">Collect each member’s preferences</h2>
          <p className="mt-2 text-sm text-slate-600">Each member enters their own budget cap, ordered interests, and preferred pace.</p></div>
        <div className="grid gap-4 lg:grid-cols-2">{group.members.map(member => <MemberPreferencesCard key={member.id} member={member}
          busy={busy} onSave={saveMember}/>)}</div>
        <button className="primary-btn" disabled={busy || !allPreferencesSaved} onClick={() => void generatePlan()}>
          {busy ? "Balancing preferences…" : result ? "Regenerate group itinerary" : "Generate fair group itinerary"}<span aria-hidden="true">↗</span>
        </button>
        {!allPreferencesSaved && <p className="text-xs text-slate-500">Save preferences for every member to continue.</p>}
      </section>

      {result && <GroupPlanResult group={group}/>}
    </>}
  </div>;
}

function GroupPlanResult({group}: {group: GroupTrip}) {
  const result = group.plan;
  if (!result) return null;
  const plan = result.itinerary;
  const days = Array.from({length: group.number_of_days}, (_, index) => {
    const day = new Date(`${group.start_date}T12:00:00Z`);
    day.setUTCDate(day.getUTCDate() + index);
    return day.toISOString().slice(0, 10);
  });
  const placesSource = plan.sources.places;

  return <section className="space-y-5" aria-live="polite">
    <div className="panel"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="eyebrow">STEP 3 · THE SHARED PLAN</p>
      <h2 className="mt-1 font-display text-2xl">Why this plan</h2><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{result.why_this_plan}</p></div>
      <span className={`rounded-full px-3 py-1.5 text-xs font-semibold ${plan.valid ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"}`}>
        {plan.valid ? "Schedule validated" : "Needs review"}</span></div>
      {!plan.activities.length && <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950" role="alert">
        <strong>No itinerary could be generated.</strong><p className="mt-1">{placesSource?.message || plan.conflicts[0] || "No activities were available for these dates."}</p>
        <p className="mt-1">The group is saved. Check the place provider and regenerate when live place data is available.</p>
      </div>}
      {!!plan.warnings.length && <details className="mt-4 rounded-lg bg-slate-50 p-3 text-sm"><summary className="cursor-pointer font-semibold">Planning notes ({plan.warnings.length})</summary>
        <ul className="mt-2 list-disc space-y-1 pl-5">{plan.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></details>}
    </div>

    <div className="grid gap-4 sm:grid-cols-2">
      <article className="panel"><p className="eyebrow">TOTAL TRIP COST</p>
        <p className="mt-2 font-display text-3xl">{result.budget.estimate_complete ? money(result.budget.total_estimate, group.currency) : "Incomplete"}</p>
        <p className="mt-2 text-sm text-slate-600">{result.budget.estimate_complete ? "Projected total from known prices and allowances." : `Known-cost lower bound: ${money(result.budget.known_total, group.currency)}. Some prices are unavailable.`}</p>
      </article>
      <article className="panel"><p className="eyebrow">ESTIMATED SHARE PER MEMBER</p>
        <p className="mt-2 font-display text-3xl">{result.budget.estimate_complete ? money(result.budget.estimated_per_member, group.currency) : money(result.budget.known_per_member, group.currency)}</p>
        <p className="mt-2 text-sm text-slate-600">{result.budget.estimate_complete ? "Equal split of the projected total." : "Known-cost share only; not a complete budget estimate."}</p>
      </article>
    </div>

    <div className="panel"><h3 className="font-display text-xl">Budget check by member</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-2">{result.budget.member_checks.map(check => <div key={check.member_id} className="rounded-lg border border-slate-200 p-3">
        <div className="flex items-center justify-between gap-3"><strong>{check.member_name}</strong>
          <span className={`text-xs font-semibold ${check.status === "over" ? "text-red-700" : check.status === "within" ? "text-emerald-700" : "text-amber-700"}`}>
            {check.status === "over" ? "Over budget" : check.status === "within" ? "Within budget" : "Cannot confirm"}</span></div>
        <p className="mt-1 text-sm text-slate-600">Budget: {money(check.budget, group.currency)} · {result.budget.estimate_complete ? "Share" : "Known share"}: {money(check.known_share, group.currency)}</p>
        <p className="mt-1 text-xs text-slate-500">{check.note}</p>
      </div>)}</div>
    </div>

    <div className="panel"><h3 className="font-display text-xl">Interest coverage</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-2">{result.member_coverage.map(item => <div key={item.member_id} className="rounded-lg bg-slate-50 p-3">
        <strong>{item.member_name}</strong><p className="mt-1 text-sm text-slate-600">Top interests: {item.top_interests.join(", ") || "None entered"}</p>
        <p className="mt-1 text-sm">Covered: {item.covered_interests.length ? item.covered_interests.join(", ") : "No top interest matched by available places"}</p>
      </div>)}</div>
    </div>

    <div className="panel"><h3 className="font-display text-xl">Conflicts and resolutions</h3>
      {!result.conflicts.length ? <p className="empty-note">No major preference conflicts were detected.</p> : <div className="mt-3 space-y-3">
        {result.conflicts.map((conflict, index) => <article key={`${conflict.conflict_type}-${index}`} className="rounded-lg border border-slate-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2"><strong className="capitalize">{conflict.conflict_type} conflict · {conflict.members.join(", ")}</strong>
            <span className={`text-xs font-semibold ${conflict.resolved ? "text-emerald-700" : "text-amber-700"}`}>{conflict.resolved ? "Resolved" : "Needs attention"}</span></div>
          <p className="mt-2 text-sm text-slate-700">{conflict.description}</p><p className="mt-1 text-sm text-slate-600">Resolution: {conflict.resolution}</p>
        </article>)}
      </div>}
    </div>

    <div className="space-y-4"><h3 className="font-display text-2xl">Shared itinerary</h3>
      {days.map((day, index) => {
        const activities = plan.activities.filter(activity => activity.date === day);
        return <article key={day} className="panel">
          <p className="eyebrow">DAY {index + 1} · {new Date(`${day}T12:00:00`).toLocaleDateString(undefined, {weekday: "long", month: "short", day: "numeric"})}</p>
          {!activities.length ? <p className="empty-note">No activities scheduled for this day.</p> : <ol className="mt-3 space-y-3">
            {activities.map(activity => <li key={activity.id} className="flex gap-4 border-t border-slate-100 pt-3">
              <span className="min-w-24 text-sm font-semibold text-teal-800">{activity.start_time}–{activity.end_time}</span>
              <div><strong>{activity.place.name}</strong><p className="text-sm text-slate-600">{activity.place.reason || activity.place.kind} · {activity.duration_minutes} min</p></div>
            </li>)}
          </ol>}
        </article>;
      })}
    </div>
  </section>;
}
