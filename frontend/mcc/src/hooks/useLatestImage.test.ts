import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useLatestImage } from "./useLatestImage";
import { createQueryWrapper } from "./testUtils";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useLatestImage", () => {
  it("returns the latest image on success", async () => {
    const image = { id: "img-1", data: "base64" };
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => image,
    } as Response);

    const { result } = renderHook(() => useLatestImage(), { wrapper: createQueryWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(image);
  });

  it("throws when the payload contains a message", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ message: "no image yet" }),
    } as Response);

    const { result } = renderHook(() => useLatestImage(), { wrapper: createQueryWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toEqual(new Error("no image yet"));
  });

  it("throws on a non-ok response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Server Error",
    } as Response);

    const { result } = renderHook(() => useLatestImage(), { wrapper: createQueryWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toEqual(new Error("API error: 500 Server Error"));
  });
});
