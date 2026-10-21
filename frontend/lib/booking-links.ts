import type { Preferences } from "@/types/live";

/** Stay details used to pre-fill booking-site searches. Dates are YYYY-MM-DD. */
export interface StayDetails {
  destination: string; checkIn: string; checkOut: string; adults: number; rooms: number;
}

export interface StayErrors {
  destination?: string; checkIn?: string; checkOut?: string; adults?: string; rooms?: string;
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const DAY_MS = 86_400_000;

function parseDate(value: string) {
  if (!ISO_DATE.test(value)) return null;
  const time = Date.parse(`${value}T00:00:00Z`);
  return Number.isNaN(time) ? null : time;
}

export function addDays(date: string, days: number) {
  const time = parseDate(date);
  return time === null ? date : new Date(time + days * DAY_MS).toISOString().slice(0, 10);
}

export function nightsBetween(checkIn: string, checkOut: string) {
  const start = parseDate(checkIn), end = parseDate(checkOut);
  return start === null || end === null ? 0 : Math.round((end - start) / DAY_MS);
}

/** Matches the planner's hotel convention: a trip of N days stays max(1, N - 1) nights. */
export function stayFromTrip(preferences: Preferences): StayDetails {
  return {
    destination: preferences.destination,
    checkIn: preferences.start_date,
    checkOut: addDays(preferences.start_date, Math.max(1, preferences.number_of_days - 1)),
    adults: preferences.travelers,
    rooms: preferences.rooms,
  };
}

/** Booking.com search results pre-filled with destination (or hotel name), dates, guests, and rooms. */
export function bookingSearchUrl(stay: StayDetails, query = stay.destination) {
  const url = new URL("https://www.booking.com/searchresults.html");
  url.searchParams.set("ss", query.trim());
  url.searchParams.set("checkin", stay.checkIn);
  url.searchParams.set("checkout", stay.checkOut);
  url.searchParams.set("group_adults", String(stay.adults));
  url.searchParams.set("no_rooms", String(stay.rooms));
  url.searchParams.set("group_children", "0");
  return url.toString();
}

export function bookingHotelUrl(stay: StayDetails, hotelName: string) {
  return bookingSearchUrl(stay, `${hotelName}, ${stay.destination}`);
}

export function validateStay(stay: StayDetails, today: string): StayErrors {
  const errors: StayErrors = {};
  if (!stay.destination.trim()) errors.destination = "Where are you staying? Enter a city, like “Jaipur, India”.";
  const start = parseDate(stay.checkIn), end = parseDate(stay.checkOut);
  if (start === null) errors.checkIn = "Choose a check-in date.";
  else if (stay.checkIn < today) errors.checkIn = "Check-in can’t be in the past.";
  if (end === null) errors.checkOut = "Choose a check-out date.";
  else if (start !== null) {
    const nights = nightsBetween(stay.checkIn, stay.checkOut);
    if (nights < 1) errors.checkOut = "Check-out needs to be at least one day after check-in.";
    else if (nights > 30) errors.checkOut = "Stays are limited to 30 nights. Try a shorter range.";
  }
  if (!Number.isInteger(stay.adults) || stay.adults < 1 || stay.adults > 30) errors.adults = "Guests must be between 1 and 30.";
  if (!Number.isInteger(stay.rooms) || stay.rooms < 1 || stay.rooms > 10) errors.rooms = "Rooms must be between 1 and 10.";
  else if (!errors.adults && stay.rooms > stay.adults) errors.rooms = "Each room needs at least one guest.";
  return errors;
}
