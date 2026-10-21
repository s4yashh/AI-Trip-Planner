import type {LivePlan} from "@/types/live";

export type GroupPace = "relaxed" | "moderate" | "packed";
export type BudgetStatus = "within" | "over" | "unknown";

export interface GroupTripCreate {
  destination: string;
  start_date: string;
  number_of_days: number;
  member_count: number;
  currency: "INR" | "USD";
  member_names?: string[];
}

export interface GroupMemberPreferences {
  budget: number | null;
  interests: string[];
  pace: GroupPace;
}

export interface GroupMember {
  id: string;
  name: string;
  preferences: GroupMemberPreferences | null;
}

export interface MemberCoverage {
  member_id: string;
  member_name: string;
  top_interests: string[];
  covered_interests: string[];
}

export interface GroupConflict {
  conflict_type: "interests" | "pace" | "budget";
  members: string[];
  description: string;
  resolution: string;
  resolved: boolean;
}

export interface MemberBudgetCheck {
  member_id: string;
  member_name: string;
  budget: number | null;
  known_share: number;
  status: BudgetStatus;
  note: string;
}

export interface GroupBudget {
  currency: "INR" | "USD";
  total_estimate: number | null;
  known_total: number;
  estimated_per_member: number | null;
  known_per_member: number;
  estimate_complete: boolean;
  member_checks: MemberBudgetCheck[];
}

export interface GroupDayPlan {
  day_number: number;
  date: string;
  pace: GroupPace;
  themes: string[];
  featured_members: string[];
  note: string;
}

export interface MemberStayCheck {
  member_id: string;
  member_name: string;
  budget: number | null;
  status: "over" | "stay_fits" | "unknown";
  note: string;
}

export interface GroupApproximateCosts {
  currency: "INR" | "USD";
  hotel_name: string;
  price_per_night: number;
  nights: number;
  rooms: number;
  stay_total: number;
  stay_per_member: number;
  approximate_total: number;
  approximate_per_member: number;
  basis: string;
  member_checks: MemberStayCheck[];
}

export interface GroupPlan {
  itinerary: LivePlan;
  why_this_plan: string;
  member_coverage: MemberCoverage[];
  conflicts: GroupConflict[];
  budget: GroupBudget;
  day_plans?: GroupDayPlan[];
  why_source?: "rules" | "ai";
  approximate_costs?: GroupApproximateCosts | null;
}

export interface GroupTrip {
  id: string;
  version: number;
  destination: string;
  start_date: string;
  number_of_days: number;
  member_count: number;
  currency: "INR" | "USD";
  members: GroupMember[];
  plan: GroupPlan | null;
  created_at: string;
  updated_at: string;
}
