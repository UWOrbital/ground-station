import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useSatelliteStatus, type SatelliteStatusResponse } from "@/hooks/useSatelliteStatus";
import { API_BASE_URL, ApiError } from "@/lib/apiClient";
import { createQueryWrapper } from "@/__tests__/testUtils";

const snapshot: SatelliteStatusResponse = {
  status: "online",
  last_contact: "2 min ago",
  session_duration: "5 min",
  telemetry_data: [{ label: "OBC Temperature", value: "42", unit: null }],
};

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useSatelliteStatus", () => {
  it("returns the status snapshot on success", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => snapshot,
    } as Response);

    const { result } = renderHook(() => useSatelliteStatus(true), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(snapshot);
  });

  it("requests the status endpoint with credentials", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => snapshot,
    } as Response);

    const { result } = renderHook(() => useSatelliteStatus(true), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(fetchSpy).toHaveBeenCalledWith(`${API_BASE_URL}/status/status`, {
      credentials: "include",
    });
  });

  it("throws an ApiError on a non-ok response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Server exploded" }),
    } as Response);

    const { result } = renderHook(() => useSatelliteStatus(true), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect(result.current.error?.message).toBe("Server exploded");
    expect((result.current.error as ApiError).status).toBe(500);
  });

  it("does not fetch when disabled", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");

    const { result } = renderHook(() => useSatelliteStatus(false), {
      wrapper: createQueryWrapper(),
    });

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(result.current.fetchStatus).toBe("idle");
  });
});
