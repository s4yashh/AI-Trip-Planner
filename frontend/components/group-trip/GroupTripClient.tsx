"use client";

import {useEffect, useState, type FormEvent} from "react";
import {addDays} from "@/lib/booking-links";
import {DEMO_DAYS, DEMO_DESTINATION, DEMO_MEMBERS} from "@/lib/group-demo";
import {groupRequest} from "@/lib/group-trip-api";
import Link from "next/link";
import type {GroupApproximateCosts, GroupMember, GroupMemberPreferences, GroupPace, GroupTrip, GroupTripCreate} from "@/types/group-trip";

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
        className="rounded-lg border border-slate-300 bg-white px-3 py-2" placeholder="e.g. beach, food, history"/>
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
  </form>;
}

export function GroupTripClient({initialGroupId}: {initialGroupId?: string}) {
  const [group, setGroup] = useState<GroupTrip | null>(null);
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState(localToday);
  const [days, setDays] = useState(3);
  const [memberCount, setMemberCount] = useState(3);
  const [currency, setCurrency] = useState<"INR" | "USD">("INR");
  const [names, setNames] = useState<string[]>([]);
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
        member_count: memberCount, currency, member_names: names.slice(0, memberCount).map(name => name.trim())};
      const saved = await groupRequest<GroupTrip>("", "POST", payload);
      setGroup(saved);
      window.history.replaceState({}, "", `/group-plan?group=${encodeURIComponent(saved.id)}`);
      setMessage("Group created. Each member can now save their own preferences.");
    } catch (reason) {setError(reason instanceof Error ? reason.message : "Could not create this group trip.");}
    finally {setBusy(false);}
  }

  async function loadDemo() {
    setBusy(true); setError(""); setMessage("");
    try {
      let saved = await groupRequest<GroupTrip>("", "POST", {destination: DEMO_DESTINATION, start_date: addDays(localToday(), 5),
        number_of_days: DEMO_DAYS, member_count: DEMO_MEMBERS.length, currency: "INR",
        member_names: DEMO_MEMBERS.map(member => member.name)} satisfies GroupTripCreate);
      for (const [index, member] of saved.members.entries()) {
        saved = await groupRequest<GroupTrip>(`/${encodeURIComponent(saved.id)}/members/${encodeURIComponent(member.id)}`,
          "PATCH", {version: saved.version, preferences: DEMO_MEMBERS[index].preferences});
      }
      setGroup(saved);
      window.history.replaceState({}, "", `/group-plan?group=${encodeURIComponent(saved.id)}`);
      setMessage("Demo group ready: three members with different budgets, interests, and paces. Generate the plan to see how conflicts are resolved.");
    } catch (reason) {setError(reason instanceof Error ? reason.message : "Could not create the demo group.");}
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
    setDays(3); setMemberCount(3); setCurrency("INR"); setNames([]);
    window.history.replaceState({}, "", "/group-plan");
  }

  if (loading) return <p className="empty-note" role="status"><span className="spinner" aria-hidden="true"/>Loading group trip…</p>;

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
            className="rounded-lg border border-slate-300 bg-white px-3 py-2" placeholder="e.g. Kochi, India"/>
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
        <fieldset className="grid gap-2">
          <legend className="text-sm font-medium text-slate-700">Member names <span className="text-xs font-normal text-slate-500">Optional, so plans read “Asha’s beach day”</span></legend>
          <div className="grid gap-2 sm:grid-cols-3">{Array.from({length: Math.min(Math.max(memberCount || 0, 0), 20)}, (_, index) =>
            <input key={index} aria-label={`Member ${index + 1} name`} maxLength={80} value={names[index] ?? ""} placeholder={`Member ${index + 1}`}
              onChange={event => setNames(previous => { const next = [...previous]; next[index] = event.target.value; return next; })}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2"/>)}</div>
        </fieldset>
        <p className="text-xs leading-5 text-slate-500">Group data is stored separately from your existing single-person trips.</p>
        <div className="flex flex-wrap items-center gap-3">
          <button className="primary-btn w-fit" disabled={busy}>{busy ? "Creating group…" : "Create group"}<span aria-hidden="true">↗</span></button>
          <button type="button" className="secondary-btn" disabled={busy} onClick={() => void loadDemo()}>Try a demo group (3 members)</button>
        </div>
      </form>
    </section> : <>
      <section className="rounded-2xl bg-[#173f3b] p-6 text-white sm:p-8">
        <p className="eyebrow text-emerald-100">SHARED TRIP</p><h2 className="mt-2 font-display text-3xl">{group.destination}</h2>
        <p className="mt-2 text-sm text-emerald-50">{group.start_date} · {group.number_of_days} days · {group.member_count} members</p>
        <p className="mt-3 text-xs text-emerald-100">Group reference: {group.id}</p>
      </section>

      <section className="space-y-4">
        <details className="space-y-4" open={!result}>
        <summary className="cursor-pointer list-none"><span className="eyebrow block">STEP 2</span><h2 className="mt-1 font-display text-2xl">Collect each member’s preferences <span className="text-sm font-normal text-slate-500">({group.members.filter(member => member.preferences).length}/{group.members.length} saved{result ? " · tap to edit" : ""})</span></h2>
          <span className="mt-2 block text-sm text-slate-600">Each member enters their own budget cap, ordered interests, and preferred pace. No account or invite link is needed.</span></summary>
        <div className="mt-4 grid gap-4 lg:grid-cols-2">{group.members.map(member => <MemberPreferencesCard key={member.id} member={member}
          busy={busy} onSave={saveMember}/>)}</div>
        </details>
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
      <h2 className="mt-1 font-display text-2xl">Why this plan</h2><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{result.why_this_plan}</p>
      <p className="mt-2 text-[11px] text-slate-500">{result.why_source === "ai" ? "Written by your AI assistant from the plan’s facts." : "Planner summary."}</p></div>
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

    {result.approximate_costs && <ApproximateCosts costs={result.approximate_costs}/>}

    <div className="panel"><h3 className="font-display text-xl">Budget check by member</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-2">{result.budget.member_checks.map(check => <div key={check.member_id} className="rounded-lg border border-slate-200 p-3">
        <div className="flex items-center justify-between gap-3"><strong>{check.member_name}</strong>
          <span className={`text-xs font-semibold ${check.status === "over" ? "text-red-700" : check.status === "within" ? "text-emerald-700" : "text-amber-700"}`}>
            {check.status === "over" ? "Over budget" : check.status === "within" ? "Within budget" : "Cannot confirm"}</span></div>
        <p className="mt-1 text-sm text-slate-600">Budget: {money(check.budget, group.currency)} · {result.budget.estimate_complete ? "Share" : "Known share"}: {money(check.known_share, group.currency)}</p>
        <p className="mt-1 text-xs text-slate-500">{check.note}</p>
        {(() => { const stay = result.approximate_costs?.member_checks.find(item => item.member_id === check.member_id);
          return stay && stay.status !== "unknown" && <p className={`mt-1 text-xs font-medium ${stay.status === "over" ? "text-red-700" : "text-emerald-700"}`}>
            {stay.status === "over" ? "⚠ Over budget on the approximate stay alone" : "Approximate stay share fits this budget"}</p>; })()}
      </div>)}</div>
    </div>

    <details className="panel group" open><summary className="cursor-pointer font-display text-xl">Interest coverage <span className="text-sm font-normal text-slate-500">· every member’s top interests</span></summary>
      <div className="mt-3 grid gap-3 md:grid-cols-2">{result.member_coverage.map(item => <div key={item.member_id} className="rounded-lg bg-slate-50 p-3">
        <strong>{item.member_name}</strong><p className="mt-1 text-sm text-slate-600">Top interests: {item.top_interests.join(", ") || "None entered"}</p>
        <p className="mt-1 text-sm">Covered: {item.covered_interests.length ? item.covered_interests.join(", ") : "No top interest matched by available places"}</p>
      </div>)}</div>
    </details>

    <div className="panel"><h3 className="font-display text-xl">Conflicts found and how they were resolved</h3>
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
        const dayPlan = result.day_plans?.find(item => item.day_number === index + 1);
        return <article key={day} className="panel">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="eyebrow">DAY {index + 1} · {new Date(`${day}T12:00:00`).toLocaleDateString(undefined, {weekday: "long", month: "short", day: "numeric"})}</p>
            {dayPlan && <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold capitalize ${PACE_STYLES[dayPlan.pace]}`}>{dayPlan.pace} pace</span>}
          </div>
          {dayPlan?.note && <p className="mt-2 text-sm font-medium text-slate-700">{dayPlan.note}</p>}
          {!activities.length ? <p className="empty-note">No activities scheduled for this day.</p> : <ol className="mt-3 space-y-3">
            {activities.map(activity => <li key={activity.id} className="flex gap-4 border-t border-slate-100 pt-3">
              <span className="min-w-24 text-sm font-semibold text-teal-800">{activity.start_time}–{activity.end_time}</span>
              <div><strong>{activity.place.name}</strong><p className="text-sm text-slate-600">{activity.place.reason || activity.place.kind} · {activity.duration_minutes} min</p></div>
            </li>)}
          </ol>}
        </article>;
      })}
    </div>

    <div className="panel"><p className="eyebrow">NEXT STEPS</p><h3 className="mt-1 font-display text-xl">Book the trip</h3>
      <p className="mt-2 text-sm text-slate-600">Open hotel and flight searches pre-filled for the whole group.</p>
      <div className="mt-4 flex flex-wrap gap-3">
        <Link className="primary-btn" href={`/hotels?${new URLSearchParams({destination: group.destination, check_in: group.start_date,
          check_out: addDays(group.start_date, Math.max(1, group.number_of_days - 1)), adults: String(group.member_count),
          rooms: String(Math.ceil(group.member_count / 2)), currency: group.currency})}`}>Find hotels for the group<span aria-hidden="true">↗</span></Link>
        <Link className="secondary-btn inline-flex items-center" href={`/flights?${new URLSearchParams({to: group.destination.split(",")[0],
          depart: group.start_date, return: addDays(group.start_date, group.number_of_days - 1), adults: String(Math.min(group.member_count, 9))})}`}>Search flights</Link>
      </div>
    </div>
  </section>;
}

const PACE_STYLES: Record<GroupPace, string> = {
  relaxed: "bg-sky-50 text-sky-800", moderate: "bg-emerald-50 text-emerald-800", packed: "bg-orange-50 text-orange-800",
};

function ApproximateCosts({costs}: {costs: GroupApproximateCosts}) {
  return <div className="panel approx-panel">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="eyebrow">APPROXIMATE SHARED STAY</p>
        <p className="mt-2 font-display text-3xl">≈ {money(Math.round(costs.stay_per_member), costs.currency)} <span className="text-base text-slate-500">per member</span></p>
        <p className="mt-1 text-sm text-slate-600">≈ {money(Math.round(costs.stay_total), costs.currency)} total at {costs.hotel_name} · {costs.rooms} room{costs.rooms === 1 ? "" : "s"} × {costs.nights} night{costs.nights === 1 ? "" : "s"} at ≈ {money(Math.round(costs.price_per_night), costs.currency)}/night</p>
        <p className="mt-1 text-sm text-slate-600">Approximate trip total with known costs: ≈ {money(Math.round(costs.approximate_total), costs.currency)} (≈ {money(Math.round(costs.approximate_per_member), costs.currency)} each)</p></div>
      <span className="source-tag source-estimated">AI estimate</span>
    </div>
    <p className="mt-3 text-xs leading-5 text-slate-500">{costs.basis} Confirm live prices before booking.</p>
  </div>;
}
