import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { usePictureRequests } from "./usePictureRequests";
import { ApiError } from "@/lib/apiClient";
import { createQueryWrapper } from "./testUtils";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("usePictureRequests", () => {
  it("returns the unwrapped request list and encodes paging in the query string", async () => {
    const requests = [
      {
        id: "11111111-1111-1111-1111-111111111111",
        aro_id: "22222222-2222-2222-2222-222222222222",
        latitude: 43.47,
        longitude: -80.54,
        created_on: "2026-01-01T00:00:00Z",
        request_sent_to_obc_on: null,
        pic_taken_on: null,
        pic_transmitted_on: null,
        delete_deadline: null,
        packet_id: null,
        status: "pending",
        operations: {},
      },
    ];
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: requests, operations: {} }),
    } as Response);

    const { result } = renderHook(() => usePictureRequests(50, 10), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(requests);

    const calledUrl = String(fetchSpy.mock.calls[0][0]);
    expect(calledUrl).toContain("/requests/?");
    expect(calledUrl).toContain("count=50");
    expect(calledUrl).toContain("offset=10");
  });

  it("throws an ApiError on a failed response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: "boom" }),
    } as Response);

    const { result } = renderHook(() => usePictureRequests(), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect((result.current.error as ApiError).status).toBe(500);
  });
});
