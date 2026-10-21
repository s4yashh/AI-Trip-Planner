import type { GroupMemberPreferences } from "@/types/group-trip";

/** Demo group: three travellers whose interests, budgets, and paces deliberately conflict. */
export const DEMO_DESTINATION = "Kochi, India";
export const DEMO_DAYS = 3;
export const DEMO_MEMBERS: {name: string; preferences: GroupMemberPreferences}[] = [
  {name: "Asha", preferences: {budget: 6000, interests: ["beach", "food", "market"], pace: "relaxed"}},
  {name: "Ravi", preferences: {budget: 3500, interests: ["trek", "nature", "viewpoint"], pace: "packed"}},
  {name: "Meera", preferences: {budget: 9000, interests: ["history", "architecture", "museum"], pace: "moderate"}},
];
