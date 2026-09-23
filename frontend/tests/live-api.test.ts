import {afterEach, describe, expect, it, vi} from "vitest";
import {emptyPreferences, money, request, safeWebsite, sourceLabel} from "@/lib/live-api";
import type {Source} from "@/types/live";

afterEach(() => vi.unstubAllGlobals());
describe("live planner state", () => {
  it("leaves missing money unknown, including initial allowances", () => {
    expect(money(null,"INR")).toBe("Unknown");
    expect(money(0,"INR")).not.toBe("Unknown");
    expect(Object.values(emptyPreferences().allowances)).toEqual([null,null,null,null,null]);
  });
  it("labels expired information stale", () => {
    const source: Source = {provider:"Weather",status:"cached",expires_at:"2026-01-01T00:00:00Z",retrieved_at:null,message:""};
    expect(sourceLabel(source,Date.parse("2026-01-02"))).toBe("stale");
  });
  it("only links to web protocols from provider text", () => {
    expect(safeWebsite("javascript:alert(1)")).toBeNull();
    expect(safeWebsite("https://example.org")).toBe("https://example.org/");
  });
  it("preserves version conflicts and structured validation errors", async () => {
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:false,status:409,json:async()=>({detail:"Reload this trip"})}));
    await expect(request("/trips/x","PATCH",{version:1})).rejects.toMatchObject({status:409,message:"Reload this trip"});
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:false,status:422,json:async()=>({detail:[{loc:["body","budget"],msg:"Must be positive"}]})}));
    await expect(request("/trips","POST",{})).rejects.toThrow("budget: Must be positive");
  });
  it("surfaces backend unavailability", async () => {
    vi.stubGlobal("fetch",vi.fn().mockRejectedValue(new TypeError("network")));
    await expect(request("/trips")).rejects.toMatchObject({status:503});
  });
});
