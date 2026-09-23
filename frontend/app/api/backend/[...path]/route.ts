import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
type Context = {params: Promise<{path: string[]}>};

async function proxy(request: NextRequest, context: Context) {
  const {path} = await context.params;
  if (!path.length || !["trips", "capabilities", "health", "chat"].includes(path[0]) || path.some(p => p === "..")) {
    return NextResponse.json({detail: "Unknown planner endpoint."}, {status: 404});
  }
  const origin = request.headers.get("origin");
  // Next's internal URL can use localhost even when the browser uses 127.0.0.1.
  let allowedOrigin = !origin;
  if (origin) {
    try { allowedOrigin = new URL(origin).host === request.headers.get("host"); }
    catch { allowedOrigin = false; }
  }
  if (request.method !== "GET" && !allowedOrigin) {
    return NextResponse.json({detail: "Request origin is not allowed."}, {status: 403});
  }
  try {
    const response = await fetch(`${process.env.AI_BACKEND_URL ?? "http://127.0.0.1:8000"}/${path.map(encodeURIComponent).join("/")}`, {
      method: request.method, headers: {"Content-Type": "application/json"}, cache: "no-store",
      body: request.method === "GET" ? undefined : await request.text(),
      signal: AbortSignal.timeout(180_000),
    });
    const body = await response.json().catch(() => ({detail: "The backend returned an unreadable response."}));
    return NextResponse.json(body, {status: response.status});
  } catch {
    return NextResponse.json({detail: "The planning backend is unreachable or timed out. Check the backend terminal and retry."}, {status: 503});
  }
}
export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
