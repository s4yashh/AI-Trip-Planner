"use client";
import dynamic from "next/dynamic";

// Dates and the saved-trip view initialize in the traveler's local timezone.
const Dashboard = dynamic(() => import("./TripDashboard").then(module => module.TripDashboard), {
  ssr: false,
  loading: () => <main className="planner-shell"><p className="empty-note">Opening your travel studio…</p></main>,
});
export function PlannerClient() { return <Dashboard/>; }
