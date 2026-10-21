import {afterEach, describe, expect, it, vi} from "vitest";
import {addDays, bookingHotelUrl, bookingSearchUrl, nightsBetween, stayFromTrip, validateStay} from "@/lib/booking-links";
import {fetchHotelSuggestions} from "@/lib/hotels-api";
import {emptyPreferences} from "@/lib/live-api";

afterEach(() => vi.unstubAllGlobals());

const stay = {destination: "Goa", checkIn: "2026-11-01", checkOut: "2026-11-04", adults: 2, rooms: 1};

describe("booking deep links", () => {
  it("pre-fills Booking.com with destination, dates, guests, and rooms", () => {
    const url = new URL(bookingSearchUrl(stay));
    expect(url.origin + url.pathname).toBe("https://www.booking.com/searchresults.html");
    expect(Object.fromEntries(url.searchParams)).toEqual({
      ss: "Goa", checkin: "2026-11-01", checkout: "2026-11-04", group_adults: "2", no_rooms: "1", group_children: "0",
    });
  });

  it("searches a specific hotel by name within the destination, safely encoded", () => {
    const url = new URL(bookingHotelUrl(stay, "Sea View & Spa"));
    expect(url.searchParams.get("ss")).toBe("Sea View & Spa, Goa");
    expect(url.search).not.toContain("& Spa");
  });

  it("derives the stay from a planned trip using the planner's nights convention", () => {
    const trip = {...emptyPreferences(), destination: "Jaipur", start_date: "2026-12-30", number_of_days: 4, travelers: 3, rooms: 2};
    expect(stayFromTrip(trip)).toEqual({destination: "Jaipur", checkIn: "2026-12-30", checkOut: "2027-01-02", adults: 3, rooms: 2});
    expect(stayFromTrip({...trip, number_of_days: 1}).checkOut).toBe("2026-12-31");
  });

  it("does date math across months and years", () => {
    expect(addDays("2026-02-27", 2)).toBe("2026-03-01");
    expect(nightsBetween("2026-12-31", "2027-01-02")).toBe(2);
    expect(nightsBetween("bad", "2027-01-02")).toBe(0);
  });
});

describe("stay validation", () => {
  const today = "2026-10-21";
  it("accepts a valid stay", () => expect(validateStay(stay, today)).toEqual({}));

  it("returns friendly messages for each problem", () => {
    const errors = validateStay({destination: " ", checkIn: "2026-10-01", checkOut: "2026-10-01", adults: 0, rooms: 0}, today);
    expect(errors.destination).toMatch(/Enter a city/);
    expect(errors.checkIn).toMatch(/past/);
    expect(errors.checkOut).toMatch(/after check-in/);
    expect(errors.adults).toBeDefined();
    expect(errors.rooms).toBeDefined();
  });

  it("limits stay length and rooms per guest", () => {
    expect(validateStay({...stay, checkOut: "2026-12-15"}, today).checkOut).toMatch(/30 nights/);
    expect(validateStay({...stay, adults: 1, rooms: 2}, today).rooms).toMatch(/at least one guest/);
  });
});

describe("hotel API client", () => {
  const search = {destination: "Goa", check_in: "2026-11-01", check_out: "2026-11-04", adults: 2, rooms: 1, currency: "INR" as const};

  it("posts the search to the separate hotel route", async () => {
    const fetch = vi.fn().mockResolvedValue({ok: true, status: 200, json: async () => ({suggestions: []})});
    vi.stubGlobal("fetch", fetch);
    await expect(fetchHotelSuggestions(search)).resolves.toEqual({suggestions: []});
    expect(fetch).toHaveBeenCalledWith("/api/hotels/suggestions", expect.objectContaining({method: "POST", body: JSON.stringify(search)}));
  });

  it("turns validation errors into readable messages", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ok: false, status: 422, json: async () => ({
      detail: [{loc: ["body"], msg: "Value error, Check-out must be at least one day after check-in"}]})}));
    await expect(fetchHotelSuggestions(search)).rejects.toMatchObject({status: 422, message: "Check-out must be at least one day after check-in"});
  });

  it("reports an unreachable backend without crashing", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));
    await expect(fetchHotelSuggestions(search)).rejects.toMatchObject({status: 503});
  });
});
