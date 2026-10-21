import type { Currency, Source } from "@/types/live";

export type HotelLabel = "Cheapest" | "Best rated" | "Best value";
export type Basis = "openstreetmap" | "ai_estimate" | "unknown";

export interface HotelSearch {
  destination: string; check_in: string; check_out: string; adults: number; rooms: number; currency: Currency;
}
export interface HotelSuggestion {
  id: string; name: string; area: string | null; distance_km: number | null;
  latitude: number | null; longitude: number | null;
  price_per_night: number | null; price_basis: Basis;
  rating: number | null; rating_basis: Basis;
  amenities: string[]; amenities_basis: Basis;
  labels: HotelLabel[]; website: string | null; verified_listing: boolean;
}
export interface HotelSuggestions {
  destination: string; check_in: string; check_out: string; nights: number; adults: number; rooms: number;
  currency: Currency; resolved_location: string | null; suggestions: HotelSuggestion[]; approximate: boolean; ai_used: boolean;
  message: string; sources: Record<string, Source>;
}
