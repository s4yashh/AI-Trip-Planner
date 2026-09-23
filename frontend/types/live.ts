export type Currency = "INR" | "USD";
export type Category = "accommodation" | "transportation" | "food" | "activities" | "miscellaneous";
export const categories: Category[] = ["accommodation", "transportation", "food", "activities", "miscellaneous"];
export interface Preferences {
  destination: string; number_of_days: number; start_date: string; budget: number | null;
  currency: Currency; interests: string[]; travelers: number; rooms: number;
  transport_mode: "walking" | "driving"; dietary_preferences: string[];
  pace: "relaxed" | "balanced" | "busy"; allowances: Record<Category, number | null>;
}
export interface Source {
  provider: string; status: "live" | "cached" | "unavailable" | "partial" | "estimated";
  retrieved_at: string | null; expires_at: string | null; message: string;
}
export interface Place {
  id: string; name: string; kind: string; latitude: number; longitude: number;
  tags: Record<string, string>; opening_hours: string | null; phone: string | null;
  website: string | null; source: Source; score: number; reason: string;
}
export interface Activity {
  id: string; place: Place; date: string; start_time: string; end_time: string;
  duration_minutes: number; duration_basis: string; locked: boolean; completed: boolean; committed: boolean;
}
export interface Route {
  from_id: string; to_id: string; minutes: number | null; distance_km: number | null;
  traffic_delay_minutes: number | null; instructions: string[]; source: Source;
}
export interface HotelOffer {
  id: string; hotel_id: string; name: string; amount: number; currency: string;
  check_in: string; check_out: string; rooms: number; source: Source;
}
export interface Budget {
  lines: {category: Category; planned: number | null; spent: number; projected: number | null; basis: string}[];
  known_total: number; total: number | null; spent: number; complete: boolean;
  within_budget: boolean | null; remaining: number | null; conversion_note: string | null;
}
export interface LivePlan {
  places: Place[]; restaurants: Place[]; lodging: Place[]; emergency: Place[]; hotels: HotelOffer[];
  weather: {date: string; temperature_min: number | null; temperature_max: number | null; rain_probability: number | null; wind_kmh: number | null; avoid_outdoor: boolean}[];
  routes: Route[]; activities: Activity[]; budget: Budget; sources: Record<string, Source>;
  agents: Record<string, string>; warnings: string[]; conflicts: string[]; valid: boolean;
  attempts: number; timezone: string; generated_at: string;
}
export interface Trip {
  id: string; version: number; preferences: Preferences; plan: LivePlan;
  expenses: {id: string; category: Category; amount: number; description: string; created_at: string}[];
  conversation: {role: "user" | "assistant"; content: string; created_at: string}[];
  monitoring: boolean; last_checked: string | null; next_check: string | null; monitoring_error: string | null;
  created_at: string; updated_at: string;
}
export interface TripSummary {
  id: string; version: number; destination: string; start_date: string;
  number_of_days: number; monitoring: boolean; valid: boolean;
}
export interface Revision {version: number; created_at: string; reason: string; before: Trip | null; after: Trip}
export interface Capabilities {local_model: {configured: boolean; message: string}; hotels_configured: boolean; traffic_configured: boolean}
