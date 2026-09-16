import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useSessionsInRange } from "@/hooks/useSessions";
import { ApiError } from "@/lib/apiClient";
import { createQueryWrapper } from "@/__tests__/testUtils";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useSessionsInRange", () => {
  it("returns the unwrapped session list and encodes the range in the query string", async () => {
    const sessions = [{ id: "s1", start_time: "2026-01-01T00:00:00Z", end_time: null }];
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: sessions }),
    } as Response);

    const after = new Date("2026-01-01T00:00:00Z");
    const before = new Date("2026-01-02T00:00:00Z");
    const { result } = renderHook(() => useSessionsInRange(after, before, 50), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 5000 });
    expect(result.current.data).toEqual(sessions);

    const calledUrl = String(fetchSpy.mock.calls[0][0]);
    expect(calledUrl).toContain("start_after=2026-01-01T00%3A00%3A00.000Z");
    expect(calledUrl).toContain("start_before=2026-01-02T00%3A00%3A00.000Z");
    expect(calledUrl).toContain("limit=50");
  }, 15000);

  it("throws an ApiError on a failed response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: "boom" }),
    } as Response);

    const { result } = renderHook(() => useSessionsInRange(new Date(), new Date()), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 }); 
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect((result.current.error as ApiError).status).toBe(500);
  }, 15000); 
});
