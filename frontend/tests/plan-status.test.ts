import {describe, expect, it} from "vitest";
import {emptyItineraryNotice} from "@/lib/plan-status";

const base = {
  activities: [],
  places: [],
  sources: {},
  conflicts: ["No feasible activities found for these dates and preferences."],
};

describe("empty itinerary messages", () => {
  it("explains place provider failures and tells the traveler the trip is saved", () => {
    const notice = emptyItineraryNotice({...base, sources: {places: {
      provider: "OpenStreetMap / Overpass", status: "unavailable",
      message: "OpenStreetMap / Overpass returned HTTP 502.",
    }}});
    expect(notice?.title).toBe("We couldn't load nearby places");
    expect(notice?.message).toContain("HTTP 502");
    expect(notice?.message).toContain("Your trip was saved");
  });

  it("distinguishes an empty search from a failed provider", () => {
    const notice = emptyItineraryNotice({...base, sources: {places: {
      provider: "OpenStreetMap / Overpass", status: "live", message: "",
    }}});
    expect(notice?.title).toBe("No nearby places were found");
  });

  it("includes source details when a live fallback returned no places", () => {
    const notice = emptyItineraryNotice({...base, sources: {places: {
      provider: "Photon / OpenStreetMap", status: "live", message: "Overpass failed; Photon returned 0 named nearby places.",
    }}});
    expect(notice?.message).toContain("Photon returned 0 named nearby places");
  });

  it("shows the scheduling conflict when places exist but no activity fits", () => {
    const notice = emptyItineraryNotice({...base, places: [{id: "p1"}]});
    expect(notice?.title).toBe("No itinerary could be scheduled");
    expect(notice?.message).toBe(base.conflicts[0]);
  });

  it("does not show an empty-plan alert when an activity exists", () => {
    expect(emptyItineraryNotice({...base, activities: [{id: "a1"}]})).toBeNull();
  });
});
