export const INTEREST_OPTIONS = [
  "History",
  "Architecture",
  "Culture",
  "Nature",
  "Food",
  "Shopping",
  "Adventure",
  "Nightlife",
] as const;

export type Interest = (typeof INTEREST_OPTIONS)[number];
export type Currency = "INR" | "USD";

export interface TripRequest {
  destination: string;
  number_of_days: number;
  budget: number;
  interests: string[];
  currency: Currency;
  start_date?: string;
}

export interface POIRecommendation {
  poi_id: string;
  name: string;
  category: string;
  recommendation_score: number;
  rating: number;
  visit_duration_hours: number;
  estimated_cost: number;
  reason: string;
}

export interface ItineraryItem {
  poi_id: string;
  name: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
  estimated_cost: number;
  travel_minutes_to_next: number | null;
  travel_source: string | null;
}

export interface ItineraryDay {
  day_number: number;
  items: ItineraryItem[];
}

export interface Itinerary {
  days: ItineraryDay[];
  skipped_poi_ids: string[];
}

export interface BudgetLine {
  category: string;
  amount: number;
  basis: string;
}

export interface BudgetAnalysis {
  accommodation: number;
  transportation: number;
  food: number;
  activities: number;
  miscellaneous: number;
  total_cost: number;
  user_budget: number | null;
  within_budget: boolean | null;
  remaining_budget: number | null;
  suggestions: string[];
  breakdown: BudgetLine[];
}

export interface AgentExecutionStatus {
  orchestrator: boolean;
  poi_recommendation: boolean;
  weather: boolean;
  restaurant: boolean;
  itinerary: boolean;
  budget: boolean;
  validator: boolean;
  lines: string[];
}

export interface TripSummary {
  destination: string;
  number_of_days: number;
  budget: number | null;
  interests: string[];
  currency: string;
  message: string;
  recommended_count: number;
  days_generated: number;
  total_estimated_cost: number | null;
}

export interface WeatherDay {
  date: string;
  day_number: number;
  temp_max_c: number | null;
  temp_min_c: number | null;
  precipitation_probability: number | null;
  condition: string;
  wind_speed_kmh: number | null;
  avoid_outdoor: boolean;
}

export interface WeatherReport {
  destination: string;
  source: string;
  message: string;
  days: WeatherDay[];
}

export interface RestaurantItem {
  restaurant_id: string;
  name: string;
  cuisine: string;
  rating: number;
  price_level: number;
  distance_km: number | null;
  restaurant_score: number;
  reason: string;
  source: string;
}

export interface RestaurantList {
  source: string;
  message: string;
  results: RestaurantItem[];
}

export interface ValidationViolation {
  code: string;
  message: string;
}

export interface ValidationReport {
  passed: boolean;
  attempts: number;
  max_attempts: number;
  notes: string[];
  violations: ValidationViolation[];
}

export interface TripResult {
  trip_summary: TripSummary;
  recommended_pois: POIRecommendation[];
  weather_report: WeatherReport | null;
  restaurant_list: RestaurantList | null;
  itinerary: Itinerary;
  budget_analysis: BudgetAnalysis | null;
  validation_report: ValidationReport | null;
  agent_execution_status: AgentExecutionStatus;
  errors: string[];
}