import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useTelemetry } from "@/hooks/useTelemetry";
import { createQueryWrapper } from "@/__tests__/testUtils";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useTelemetry", () => {
  it("returns telemetry data on success", async () => {
    const payload = { data: [{ id: "1" }] };
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => payload,
    } as Response);

    const { result } = renderHook(() => useTelemetry(), { wrapper: createQueryWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(payload);
  });

  it("surfaces an error when the response is not ok", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: false } as Response);

    const { result } = renderHook(() => useTelemetry(), { wrapper: createQueryWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toEqual(new Error("Failed to fetch telemetry"));
  });
});
