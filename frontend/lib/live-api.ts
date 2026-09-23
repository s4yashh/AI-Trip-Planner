import type { Preferences, Source } from "@/types/live";

export class RequestError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/backend${path}`, {method, cache: "no-store",
      headers: body ? {"Content-Type": "application/json"} : undefined,
      body: body ? JSON.stringify(body) : undefined});
  } catch {
    throw new RequestError("Cannot reach the planner. Check that the application is running.", 503);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail ?? data?.error;
    const message = typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((entry: {loc?: string[]; msg?: string}) => `${entry.loc?.slice(1).join(".")}: ${entry.msg}`).join("; ")
      : `Request failed (${response.status}).`;
    throw new RequestError(message, response.status);
  }
  if (data === null) throw new RequestError("The planner returned an unreadable response.", 502);
  return data as T;
}

export function emptyPreferences(): Preferences {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
  return {destination: "", start_date: local, number_of_days: 3, budget: null, currency: "INR", interests: [],
    travelers: 1, rooms: 1, transport_mode: "walking", dietary_preferences: [], pace: "balanced",
    allowances: {accommodation: null, transportation: null, food: null, activities: null, miscellaneous: null}};
}

export function money(value: number | null | undefined, currency: string) {
  return value == null ? "Unknown" : new Intl.NumberFormat("en-IN", {style: "currency", currency, maximumFractionDigits: 2}).format(value);
}

export function sourceLabel(source: Source, now = Date.now()) {
  return source.expires_at && Date.parse(source.expires_at) < now ? "stale" : source.status;
}

export function safeWebsite(value: string | null) {
  if (!value) return null;
  try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) ? url.href : null; }
  catch { return null; }
}
