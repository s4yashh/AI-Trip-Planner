/** Skyscanner deep links. No flight prices are fetched or shown by this app. */
export type Cabin = "economy" | "premiumeconomy" | "business" | "first";

export interface FlightSearch {
  from: string; to: string; depart: string; returnDate: string | null; adults: number; cabin: Cabin; directOnly: boolean;
}

export interface FlightErrors { from?: string; to?: string; depart?: string; returnDate?: string; adults?: string }

export const CABINS: {value: Cabin; label: string}[] = [
  {value: "economy", label: "Economy"}, {value: "premiumeconomy", label: "Premium economy"},
  {value: "business", label: "Business"}, {value: "first", label: "First"},
];

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const IATA = /^[A-Z]{3}$/;

/** Skyscanner's path date format: 2026-11-10 -> 261110. */
export function skyscannerDate(date: string) {
  return date.slice(2).replaceAll("-", "");
}

export function skyscannerUrl(search: FlightSearch) {
  const segments = [search.from.toLowerCase(), search.to.toLowerCase(), skyscannerDate(search.depart)];
  if (search.returnDate) segments.push(skyscannerDate(search.returnDate));
  const url = new URL(`https://www.skyscanner.net/transport/flights/${segments.join("/")}/`);
  url.searchParams.set("adultsv2", String(search.adults));
  url.searchParams.set("cabinclass", search.cabin);
  url.searchParams.set("rtn", search.returnDate ? "1" : "0");
  url.searchParams.set("preferdirects", String(search.directOnly));
  return url.toString();
}

export function validateFlightSearch(search: FlightSearch, today: string): FlightErrors {
  const errors: FlightErrors = {};
  if (!search.from) errors.from = "Where are you flying from? Pick an airport from the list or type its 3-letter code.";
  else if (!IATA.test(search.from)) errors.from = "We don’t recognise that airport. Pick one from the list or type its 3-letter code, like DEL.";
  if (!search.to) errors.to = "Where are you flying to? Pick an airport from the list or type its 3-letter code.";
  else if (!IATA.test(search.to)) errors.to = "We don’t recognise that airport. Pick one from the list or type its 3-letter code, like GOI.";
  if (!errors.from && !errors.to && search.from === search.to) errors.to = "Departure and arrival airports need to be different.";
  if (!ISO_DATE.test(search.depart)) errors.depart = "Choose a departure date.";
  else if (search.depart < today) errors.depart = "The departure date can’t be in the past.";
  if (search.returnDate !== null) {
    if (!ISO_DATE.test(search.returnDate)) errors.returnDate = "Choose a return date, or switch to one-way.";
    else if (!errors.depart && search.returnDate < search.depart) errors.returnDate = "Return needs to be on or after the departure date.";
  }
  if (!Number.isInteger(search.adults) || search.adults < 1 || search.adults > 9) errors.adults = "Passengers must be between 1 and 9.";
  return errors;
}
