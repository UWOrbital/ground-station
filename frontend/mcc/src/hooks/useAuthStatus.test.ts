import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useAuthStatus } from "./useAuthStatus";
import { createQueryWrapper } from "./testUtils";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useAuthStatus", () => {
  it("resolves to true when the ping succeeds", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: true } as Response);

    const { result } = renderHook(() => useAuthStatus(), { wrapper: createQueryWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe(true);
  });

  it("resolves to false when the ping fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: false } as Response);

    const { result } = renderHook(() => useAuthStatus(), { wrapper: createQueryWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe(false);
  });

  it("resolves to false when fetch rejects", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));

    const { result } = renderHook(() => useAuthStatus(), { wrapper: createQueryWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe(false);
  });
});
