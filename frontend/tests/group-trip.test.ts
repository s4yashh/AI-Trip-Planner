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
