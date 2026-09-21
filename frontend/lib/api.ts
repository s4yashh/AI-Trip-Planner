import type { TripRequest, TripResult } from "@/types/trip";

const FALLBACK_ENDPOINT = "/api/trip";

const MESSAGES: Record<number, string> = {
  400: "Your request could not be processed. Please check the details and try again.",
  422: "Some of the trip details are invalid. Please adjust them and try again.",
  503: "The AI planning service is currently unavailable. Please try again later.",
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function resolveEndpoint(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL;
  return configured && configured.trim() ? configured.trim() : FALLBACK_ENDPOINT;
}

export async function planTrip(
  request: TripRequest,
  signal?: AbortSignal,
): Promise<TripResult> {
  let response: Response;
  try {
    response = await fetch(resolveEndpoint(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal,
    });
  } catch (reason) {
    if (reason instanceof DOMException && reason.name === "AbortError") {
      throw reason;
    }
    throw new ApiError(
      "The AI planning service could not be reached. Please try again.",
    );
  }

  let data: unknown = {};
  try {
    data = await response.json();
  } catch {
    throw new ApiError(
      "The planning service returned an unreadable response. Please try again.",
      response.status,
    );
  }

  if (!response.ok) {
    const detail = extractDetail(data);
    throw new ApiError(detail ?? MESSAGES[response.status] ?? "Something went wrong while creating your trip. Please try again.", response.status);
  }

  return data as TripResult;
}

function extractDetail(data: unknown): string | undefined {
  if (
    typeof data === "object" &&
    data !== null &&
    "error" in data &&
    typeof (data as { error: unknown }).error === "string" &&
    ((data as { error: string }).error.trim().length > 0)
  ) {
    return (data as { error: string }).error;
  }
  if (
    typeof data === "object" &&
    data !== null &&
    "detail" in data &&
    typeof (data as { detail: unknown }).detail === "string"
  ) {
    return (data as { detail: string }).detail;
  }
  return undefined;
}