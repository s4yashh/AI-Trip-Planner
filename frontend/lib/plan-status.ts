import type {Source} from "@/types/live";

type EmptyItineraryPlan = {
  activities: unknown[];
  places: unknown[];
  sources: Record<string, Pick<Source, "provider" | "status" | "message">>;
  conflicts: string[];
};

export function emptyItineraryNotice(plan: EmptyItineraryPlan) {
  if (plan.activities.length) return null;

  const placesSource = plan.sources.places;
  if (placesSource?.status === "unavailable") {
    return {
      title: "We couldn't load nearby places",
      message: `${placesSource.provider} is unavailable${placesSource.message ? `: ${placesSource.message}` : "."} Your trip was saved, but an itinerary needs place data. Retry when the provider is available again.`,
    };
  }

  if (!plan.places.length) {
    const sourceMessage = plan.sources.places?.message;
    return {
      title: "No nearby places were found",
      message: `${sourceMessage ? `${sourceMessage} ` : "The place search returned no attractions for this destination. "}Check the city name or retry when place data is available.`,
    };
  }

  return {
    title: "No itinerary could be scheduled",
    message: plan.conflicts[0] || "Places were found, but none fit the trip dates and preferences. Try different dates or a more relaxed pace.",
  };
}
