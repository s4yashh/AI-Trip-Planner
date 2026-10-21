import {describe, expect, it} from "vitest";
import {AIRPORTS, airportByCode, resolveAirport, searchAirports} from "@/lib/airports";
import {skyscannerDate, skyscannerUrl, validateFlightSearch, type FlightSearch} from "@/lib/flight-links";

const search: FlightSearch = {from: "DEL", to: "GOI", depart: "2026-11-10", returnDate: "2026-11-14", adults: 2, cabin: "economy", directOnly: false};

describe("Skyscanner deep links", () => {
  it("builds a pre-filled round-trip search", () => {
    expect(skyscannerUrl(search)).toBe(
      "https://www.skyscanner.net/transport/flights/del/goi/261110/261114/?adultsv2=2&cabinclass=economy&rtn=1&preferdirects=false");
  });

  it("builds a one-way search with cabin and direct preference", () => {
    const url = new URL(skyscannerUrl({...search, returnDate: null, cabin: "business", directOnly: true, adults: 1}));
    expect(url.pathname).toBe("/transport/flights/del/goi/261110/");
    expect(Object.fromEntries(url.searchParams)).toEqual({adultsv2: "1", cabinclass: "business", rtn: "0", preferdirects: "true"});
  });

  it("formats dates as yymmdd", () => expect(skyscannerDate("2027-01-05")).toBe("270105"));
});

describe("flight search validation", () => {
  const today = "2026-10-21";
  it("accepts a valid search", () => expect(validateFlightSearch(search, today)).toEqual({}));

  it("explains each problem in plain language", () => {
    const errors = validateFlightSearch({...search, from: "", to: "PARIS", depart: "2026-10-01", adults: 0}, today);
    expect(errors.from).toMatch(/Where are you flying from/);
    expect(errors.to).toMatch(/don’t recognise/);
    expect(errors.depart).toMatch(/past/);
    expect(errors.adults).toMatch(/1 and 9/);
  });

  it("rejects same airports and a return before departure", () => {
    expect(validateFlightSearch({...search, to: "DEL"}, today).to).toMatch(/different/);
    expect(validateFlightSearch({...search, returnDate: "2026-11-09"}, today).returnDate).toMatch(/on or after/);
    expect(validateFlightSearch({...search, returnDate: "2026-11-10"}, today)).toEqual({});
  });
});

describe("airport lookup", () => {
  it("has unique, valid codes", () => {
    const codes = AIRPORTS.map(airport => airport.code);
    expect(new Set(codes).size).toBe(codes.length);
    expect(codes.every(code => /^[A-Z]{3}$/.test(code))).toBe(true);
  });

  it("ranks exact code and city matches first, ignoring accents and case", () => {
    expect(searchAirports("goi")[0].code).toBe("GOI");
    expect(searchAirports("goa").map(airport => airport.code)).toEqual(["GOI", "GOX"]);
    expect(searchAirports("sao paulo")[0].code).toBe("GRU");
    expect(searchAirports("london").map(airport => airport.code)).toEqual(["LHR", "LGW"]);
    expect(searchAirports("")).toEqual([]);
  });

  it("resolves picked labels, typed codes, and city names", () => {
    expect(resolveAirport("Goa (GOX)")).toBe("GOX");
    expect(resolveAirport(" xyz ")).toBe("XYZ");
    expect(resolveAirport("delhi")).toBe("DEL");
    expect(resolveAirport("Atlantis")).toBeNull();
    expect(airportByCode("bom")?.city).toBe("Mumbai");
  });
});
