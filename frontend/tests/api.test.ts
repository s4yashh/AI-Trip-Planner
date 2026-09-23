import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, planTrip } from "../lib/api";
import type { TripResult } from "../types/trip";

function buildResult(): TripResult {
  return {
    trip_summary: {
      destination: "Jaipur",
      number_of_days: 3,
      budget: 30000,
      interests: ["History", "Culture"],
      currency: "INR",
      message: "Personalised 3-day trip to Jaipur.",
      recommended_count: 3,
      days_generated: 3,
      total_estimated_cost: 24000,
    },
    recommended_pois: [
      {
        poi_id: "POI041",
        name: "Amber Fort",
        category: "Fort",
        recommendation_score: 0.95,
        rating: 4.8,
        visit_duration_hours: 3,
        estimated_cost: 500,
        reason: "Strong match with selected interests: history, culture.",
      },
    ],
    itinerary: {
      days: [
        {
          day_number: 1,
          items: [
            {
              poi_id: "POI041",
              name: "Amber Fort",
              start_time: "09:00",
              end_time: "12:00",
              duration_hours: 3,
              estimated_cost: 500,
              travel_minutes_to_next: null,
              travel_source: null,
            },
          ],
        },
      ],
      skipped_poi_ids: [],
    },
    weather_report: {
      destination: "Jaipur",
      source: "unavailable",
      message: "Live weather unavailable.",
      days: [],
    },
    restaurant_list: {
      source: "dataset",
      message: "Ranked local dataset restaurants.",
      results: [],
    },
    validation_report: {
      passed: true,
      attempts: 1,
      max_attempts: 3,
      notes: [],
      violations: [],
    },
    budget_analysis: {
      accommodation: 12000,
      transportation: 3000,
      food: 4500,
      activities: 3000,
      miscellaneous: 1500,
      total_cost: 24000,
      user_budget: 30000,
      within_budget: true,
      remaining_budget: 6000,
      suggestions: ["Choose a mid-range hotel."],
      breakdown: [
        { category: "Accommodation", amount: 12000, basis: "3 nights x 4000" },
      ],
    },
    agent_execution_status: {
      orchestrator: true,
      poi_recommendation: true,
      weather: true,
      restaurant: true,
      itinerary: true,
      budget: true,
      validator: true,
      lines: ["Recommendation agent completed."],
    },
    errors: [],
  };
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("planTrip", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  const request = {
    destination: "Jaipur",
    number_of_days: 3,
    budget: 30000,
    interests: ["History", "Culture"],
    currency: "INR" as const,
  };

  it("should POST to the default /api/trip endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(buildResult()));
    vi.stubGlobal("fetch", fetchMock);

    await planTrip(request);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/trip");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body)).toEqual(request);
  });

  it("should return the parsed trip result on success", async () => {
    const result = buildResult();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(result)));

    await expect(planTrip(request)).resolves.toEqual(result);
  });

  it("should throw an ApiError with a friendly message on network failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );

    const error = await planTrip(request).catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toContain("could not be reached");
  });

  it("should surface a backend error detail on a 502", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ error: "AI backend error (502)." }, 502),
      ),
    );

    const error = await planTrip(request).catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(502);
  });

  it("should surface a FastAPI validation detail on a 422", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          { detail: "Some of the trip details are invalid." },
          422,
        ),
      ),
    );

    const error = await planTrip(request).catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toContain("invalid");
    expect((error as ApiError).status).toBe(422);
  });

  it("should throw a friendly error when the response is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("<html>oops</html>", { status: 200 })),
    );

    const error = await planTrip(request).catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toContain("unreadable response");
  });

  it("should throw a generic ApiError for an unexpected status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({}, 500)));

    const error = await planTrip(request).catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toContain("Something went wrong");
  });
});