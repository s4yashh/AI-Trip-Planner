"use client";

import { useEffect, useRef, useState } from "react";
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

function section(title: string, children: React.ReactNode) {
  return (
    <section className="mt-10">
      <h2 className="mb-4 text-xl font-bold text-slate-900">{title}</h2>
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

      {section(
        "Recommended Places",
        hasPlaces ? (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {result.recommended_pois.map((recommendation) => (
              <RecommendationCard
                key={recommendation.poi_id}
                recommendation={recommendation}
                currency={currency}
              />
            ))}
          </div>
        ) : (
          <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600 shadow-sm">
            No matching places were found for this destination and interests.
            Try a different destination or add more interests.
          </p>
        ),
      )}

      {result.itinerary.days.length > 0
        ? section("Your Day-by-Day Itinerary", (
            <ItineraryCard itinerary={result.itinerary} currency={currency} />
          ))
        : null}

      {result.budget_analysis
        ? section("Budget Analysis", (
            <BudgetSummary analysis={result.budget_analysis} currency={currency} />
          ))
        : null}

      {section(
        "How this plan was built",
        <AgentStatus status={result.agent_execution_status} />,
      )}
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

  useEffect(() => {
    if (state.kind === "success") {
      try {
        localStorage.setItem(
          "ai-trip-planner:last-plan",
          JSON.stringify(state.result),
        );
      } catch {
        // storage unavailable; skip caching
      }
    }
  }, [state]);

  async function handleSubmit(payload: TripFormPayload) {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ kind: "loading" });

    try {
      const result = await planTrip(payload, controller.signal);
      setState({ kind: "success", result });
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
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          Plan Your Trip
        </h1>
        <p className="mt-2 text-slate-600">
          Tell us where you want to go, your budget, days, and interests. Your
          trip is planned by AI agents and may take a few seconds.
        </p>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-10 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <TripForm
              onSubmit={handleSubmit}
              disabled={state.kind === "loading"}
            />
            <div className="mt-6 border-t border-slate-100 pt-4">
              <p className="text-xs leading-relaxed text-slate-500">
                Prices are converted with a fixed prototype rate. Your plan is
                generated live by the backend agents — nothing is staged or
                hardcoded in this app.
              </p>
            </div>
          </div>
        </div>

        <div className="lg:col-span-3">
          {state.kind === "idle" ? (
            <p className="rounded-xl border border-dashed border-slate-300 bg-white/60 p-8 text-center text-sm text-slate-500">
              Fill in the form to see your personalized trip plan here.
            </p>
          ) : null}

          {state.kind === "loading" ? <LoadingState /> : null}

          {state.kind === "success" ? <Results result={state.result} /> : null}

          {state.kind === "error" ? (
            <div
              className="rounded-xl border border-red-200 bg-red-50 p-5"
              role="alert"
            >
              <p className="font-semibold text-red-800">Could not plan your trip</p>
              <p className="mt-1 text-sm text-red-700">{state.message}</p>
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}