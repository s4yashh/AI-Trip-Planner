import {afterEach, describe, expect, it, vi} from "vitest";
import {groupRequest} from "@/lib/group-trip-api";

afterEach(() => vi.unstubAllGlobals());

describe("group-trip API client", () => {
  it("posts to the separate group-trip route and sends member data", async () => {
    const fetch = vi.fn().mockResolvedValue({ok: true, status: 201, json: async () => ({id: "group-1"})});
    vi.stubGlobal("fetch", fetch);
    await expect(groupRequest<{id: string}>("", "POST", {destination: "Goa", member_count: 3}))
      .resolves.toEqual({id: "group-1"});
    expect(fetch).toHaveBeenCalledWith("/api/group-trips", expect.objectContaining({
      method: "POST", body: JSON.stringify({destination: "Goa", member_count: 3}),
    }));
  });

  it("preserves group API error messages", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false, status: 409, json: async () => ({detail: "Reload the group trip"}),
    }));
    await expect(groupRequest("/group-1", "GET")).rejects.toMatchObject({
      status: 409, message: "Reload the group trip",
    });
  });
});

describe("demo group data", async () => {
  const {DEMO_MEMBERS} = await import("@/lib/group-demo");
  it("has three members whose budgets, paces, and top interests all differ", () => {
    expect(DEMO_MEMBERS).toHaveLength(3);
    for (const key of ["budget", "pace"] as const) {
      expect(new Set(DEMO_MEMBERS.map(member => member.preferences[key])).size).toBe(3);
    }
    expect(new Set(DEMO_MEMBERS.map(member => member.preferences.interests[0])).size).toBe(3);
    expect(DEMO_MEMBERS.map(member => member.preferences.interests[0])).toEqual(["beach", "trek", "history"]);
  });
});
