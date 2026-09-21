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
  itinerary: boolean;
  budget: boolean;
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

export interface TripResult {
  trip_summary: TripSummary;
  recommended_pois: POIRecommendation[];
  itinerary: Itinerary;
  budget_analysis: BudgetAnalysis | null;
  agent_execution_status: AgentExecutionStatus;
  errors: string[];
}