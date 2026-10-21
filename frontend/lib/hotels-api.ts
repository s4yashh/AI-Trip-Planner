import type { HotelSearch, HotelSuggestions } from "@/types/hotels";

export class HotelRequestError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

export async function fetchHotelSuggestions(search: HotelSearch, signal?: AbortSignal): Promise<HotelSuggestions> {
  let response: Response;
  try {
    response = await fetch("/api/hotels/suggestions", {
      method: "POST", cache: "no-store", signal,
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(search),
    });
  } catch (reason) {
    if (reason instanceof DOMException && reason.name === "AbortError") throw reason;
    throw new HotelRequestError("Cannot reach hotel suggestions. Check that the application is running.", 503);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((entry: {msg?: string}) => entry.msg?.replace(/^Value error, /, "")).filter(Boolean).join("; ")
      : `Hotel search failed (${response.status}).`;
    throw new HotelRequestError(message || `Hotel search failed (${response.status}).`, response.status);
  }
  if (data === null) throw new HotelRequestError("Hotel suggestions returned an unreadable response.", 502);
  return data as HotelSuggestions;
}
