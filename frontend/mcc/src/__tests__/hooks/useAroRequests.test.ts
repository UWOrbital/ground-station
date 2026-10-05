import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useAroRequests } from "@/hooks/useAroRequests";
import { ApiError } from "@/lib/apiClient";
import { createQueryWrapper } from "@/__tests__/testUtils";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useAroRequests", () => {
  it ("returns the unwrapped ARO request list", async () => {
    const requests = [
      { id: "r1", aro_id: "u1", latitude: 47.5, longitude: -122.3,
        created_on: "2026-01-01T00:00:00Z", status: "pending" },
    ];
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: requests }),
    } as Response);

    const count = 100;
    const offset = 0;
    const { result } = renderHook(() => useAroRequests(count, offset), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 5000 });
    expect(result.current.data).toEqual(requests);

    const calledUrl = String(fetchSpy.mock.calls[0][0]);
    expect(calledUrl).toContain("count=100");
    expect(calledUrl).toContain("offset=0");
  }, 15000);

  it("throws an ApiError on a failed response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: "boom" }),
    } as Response);

    const { result } = renderHook(() => useAroRequests(100, 0), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect((result.current.error as ApiError).status).toBe(500);
  }, 15000);
});
