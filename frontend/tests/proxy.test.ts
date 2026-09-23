import {afterEach, expect, it, vi} from "vitest";
import {NextRequest} from "next/server";
import {POST} from "@/app/api/backend/[...path]/route";

afterEach(() => vi.unstubAllGlobals());
it("accepts the browser's loopback host even when Next normalizes its internal URL", async () => {
  vi.stubGlobal("fetch",vi.fn().mockResolvedValue({status:409,json:async()=>({detail:"stale version"})}));
  const request = new NextRequest("http://localhost:3000/api/backend/trips", {method:"POST",body:"{}",
    headers:{Origin:"http://127.0.0.1:3000",Host:"127.0.0.1:3000"}});
  const response = await POST(request,{params:Promise.resolve({path:["trips"]})});
  expect(response.status).toBe(409);
  expect(await response.json()).toEqual({detail:"stale version"});
});
it("rejects requests from unrelated browser origins", async () => {
  const request = new NextRequest("http://localhost:3000/api/backend/trips", {method:"POST",body:"{}",
    headers:{Origin:"https://unrelated.example",Host:"localhost:3000"}});
  expect((await POST(request,{params:Promise.resolve({path:["trips"]})})).status).toBe(403);
});
