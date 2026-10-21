export class GroupRequestError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

export async function groupRequest<T>(path = "", method = "GET", body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/group-trips${path}`, {
      method,
      cache: "no-store",
      headers: body ? {"Content-Type": "application/json"} : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new GroupRequestError("Cannot reach group planning. Check that the application is running.", 503);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    throw new GroupRequestError(typeof detail === "string" ? detail : `Group request failed (${response.status}).`, response.status);
  }
  if (data === null) throw new GroupRequestError("The group planner returned an unreadable response.", 502);
  return data as T;
}
