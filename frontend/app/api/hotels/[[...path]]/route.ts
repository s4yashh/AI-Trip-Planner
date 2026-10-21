import {NextRequest, NextResponse} from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
type Context = {params: Promise<{path?: string[]}>};

export async function POST(request: NextRequest, context: Context) {
  const {path = []} = await context.params;
  if (path.length !== 1 || path[0] !== "suggestions") {
    return NextResponse.json({detail: "Unknown hotel endpoint."}, {status: 404});
  }
  const origin = request.headers.get("origin");
  let allowedOrigin = !origin;
  if (origin) {
    try { allowedOrigin = new URL(origin).host === request.headers.get("host"); }
    catch { allowedOrigin = false; }
  }
  if (!allowedOrigin) return NextResponse.json({detail: "Request origin is not allowed."}, {status: 403});
  try {
    const response = await fetch(`${process.env.AI_BACKEND_URL ?? "http://127.0.0.1:8000"}/hotels/suggestions`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      cache: "no-store",
      body: await request.text(),
      signal: AbortSignal.timeout(120_000),
    });
    const body = await response.json().catch(() => ({detail: "Hotel suggestions returned an unreadable response."}));
    return NextResponse.json(body, {status: response.status});
  } catch {
    return NextResponse.json({detail: "The hotel suggestion backend is unreachable or timed out."}, {status: 503});
  }
}
