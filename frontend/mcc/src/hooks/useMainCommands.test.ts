import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useMainCommands } from "./useMainCommands";
import { createQueryWrapper } from "./testUtils";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useMainCommands", () => {
  it("returns the unwrapped main command list", async () => {
    const mainCommands = [{ id: 1, name: "PING", data_size: 0, total_size: 4, priority: 1 }];
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: mainCommands }),
    } as Response);

    const { result } = renderHook(() => useMainCommands(), { wrapper: createQueryWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mainCommands);
  });
});
