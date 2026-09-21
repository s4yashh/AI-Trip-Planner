"use client";

import { useRef, useState } from "react";
import { TripForm, type TripFormPayload } from "@/components/TripForm";
import { TripOverview } from "@/components/TripOverview";
import { RecommendationCard } from "@/components/RecommendationCard";
import { ItineraryCard } from "@/components/ItineraryCard";
import { BudgetSummary } from "@/components/BudgetSummary";
import { AgentStatus } from "@/components/AgentStatus";
import { LoadingState } from "@/components/LoadingState";
import { ApiError, planTrip } from "@/lib/api";
import type { TripResult } from "@/types/trip";

type PlanState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; result: TripResult }
  | { kind: "error"; message: string };

function Section({ kicker, title, children }: { kicker?: boolean; title: string; children: React.ReactNode }) {
  return (
    <section className="mt-12">
      <div className="mb-5 flex items-center gap-3">
        {kicker ? <span className="h-px w-6 bg-[#f26b4f]" aria-hidden="true" /> : null}
        <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900">
          {title}
        </h2>
      </div>
      {children}
    </section>
  );
}

function Results({ result }: { result: TripResult }) {
  const currency = result.trip_summary.currency;
  const hasPlaces = result.trip_summary.recommended_count > 0;

  return (
    <>
      <TripOverview summary={result.trip_summary} />

      <Section kicker title="Your custom picks &mdash; recommended places">
        {hasPlaces ? (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {result.recommended_pois.map((recommendation, index) => (
              <RecommendationCard
                key={recommendation.poi_id}
                recommendation={recommendation}
                currency={currency}
                rank={index + 1}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-slate-600">
              No matching places were found for this destination and interests.
              Try a different destination or add more interests.
            </p>
          </div>
        )}
      </Section>

      {result.itinerary.days.length > 0 ? (
        <Section kicker title="Day-by-day itinerary">
          <ItineraryCard itinerary={result.itinerary} currency={currency} />
        </Section>
      ) : null}

      {result.budget_analysis ? (
        <Section kicker title="How the budget stacks up">
          <BudgetSummary analysis={result.budget_analysis} currency={currency} />
        </Section>
      ) : null}

      <Section kicker title="The agents behind this plan">
        <AgentStatus status={result.agent_execution_status} />
      </Section>
    </>
  );
}

export default function PlanPage() {
  const [state, setState] = useState<PlanState>(() => {
    try {
      const saved = localStorage.getItem("ai-trip-planner:last-plan");
      if (saved) {
        return { kind: "success", result: JSON.parse(saved) as TripResult };
      }
    } catch {
      // corrupted saved plan: start fresh
    }
    return { kind: "idle" };
  });
  const abortRef = useRef<AbortController | null>(null);
  const [, forceRender] = useState(0);

  function resetAndGo() {
    try {
      localStorage.removeItem("ai-trip-planner:last-plan");
    } catch {
      // ignore
    }
    setState({ kind: "idle" });
    forceRender((n) => n + 1);
  }

  async function handleSubmit(payload: TripFormPayload) {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ kind: "loading" });

    try {
      const result = await planTrip(payload, controller.signal);
      setState({ kind: "success", result });
      try {
        localStorage.setItem("ai-trip-planner:last-plan", JSON.stringify(result));
      } catch {
        // storage unavailable; skip caching
      }
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError") {
        return;
      }
      if (reason instanceof ApiError) {
        setState({ kind: "error", message: reason.message });
      } else {
        setState({
          kind: "error",
          message: "Something unexpected went wrong. Please try again.",
        });
      }
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
      <div className="relative overflow-hidden rounded-3xl bg-[#17233d] px-6 py-10 text-center text-white sm:px-10">
        <div className="travel-grid absolute inset-0 opacity-50" aria-hidden="true" />
        <div className="pointer-events-none absolute -right-16 -top-20 h-64 w-64 rounded-full bg-[#f26b4f]/25 blur-3xl" aria-hidden="true" />
        <div className="relative mx-auto max-w-2xl">
        <p className="text-xs font-semibold uppercase tracking-widest text-[#ffb08e]">
          Your personal travel studio
        </p>
        <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
          Plan a trip worth remembering
        </h1>
        <p className="mt-3 text-slate-300">
          Tell us where, for how long, your budget, and what you love — the
          agents handle the rest.
        </p>
        </div>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-10 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <div className="overflow-hidden rounded-2xl border border-[#e9e2d3] bg-white shadow-lg shadow-slate-900/5">
            <div className="bg-gradient-to-r from-[#0b3954] to-[#0f766e] px-6 py-5">
              <h2 className="font-display text-lg font-semibold text-white">
                Trip details
              </h2>
              <p className="text-xs text-teal-50/80">
                An example: Jaipur, 3 days, ₹30,000, History + Architecture.
              </p>
            </div>
            <div className="px-6 py-6">
              <TripForm
                onSubmit={handleSubmit}
                disabled={state.kind === "loading"}
              />
            </div>
            <div className="border-t border-slate-100 px-6 py-4">
              <p className="text-xs leading-relaxed text-slate-500">
                Prices use a fixed prototype rate. Your plan is generated live
                by the backend agents — nothing is staged in this app.
              </p>
            </div>
          </div>
        </div>

        <div className="lg:col-span-3">
          {state.kind === "idle" ? (
            <div className="flex h-full min-h-80 flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#d9d1c1] bg-white/60 p-8 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#f26b4f]/10 text-[#d95b43]" aria-hidden="true">
                <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 21s-7-5.1-7-11a7 7 0 0 1 14 0c0 5.9-7 11-7 11z" />
                  <circle cx="12" cy="10" r="2.5" />
                </svg>
              </span>
              <p className="mt-4 font-display text-xl font-semibold text-slate-700">
                Your plan appears here
              </p>
              <p className="mt-1.5 max-w-sm text-sm text-slate-500">
                Fill in the form and generate your trip to see the ranked
                places, itinerary, and budget.
              </p>
            </div>
          ) : null}

          {state.kind === "loading" ? <LoadingState /> : null}

          {state.kind === "success" ? (
            <div className="animate-fade-up">
              <Results result={state.result} />
              <div className="mt-8 text-center">
                <button
                  type="button"
                  onClick={resetAndGo}
                  className="inline-flex items-center gap-2 rounded-xl border border-[#d9d1c1] bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:border-[#0f766e] hover:text-[#0f766e]"
                >
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                    <path d="M3 3v5h5" />
                  </svg>
                  Plan another trip
                </button>
              </div>
            </div>
          ) : null}

          {state.kind === "error" ? (
            <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-red-200 bg-red-50 px-8 py-14 text-center">
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-600" aria-hidden="true">
                <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M12 9v4M12 17h.01" />
                  <path d="M10.3 3.6 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0z" />
                </svg>
              </span>
              <p className="font-display text-xl font-semibold text-red-800">
                Could not plan your trip
              </p>
              <p className="max-w-sm text-sm text-red-700">{state.message}</p>
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}
