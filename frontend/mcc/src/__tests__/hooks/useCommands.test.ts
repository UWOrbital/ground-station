import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import {
  useCommandsBySession,
  useCreateCommand,
  useUpdateCommand,
  useDeleteCommand,
} from "@/hooks/useCommands";
import { ApiError } from "@/lib/apiClient";
import { createQueryWrapper } from "@/__tests__/testUtils";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useCommandsBySession", () => {
  it("is disabled when no session id is provided", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");

    const { result } = renderHook(() => useCommandsBySession(null), {
      wrapper: createQueryWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("fetches and unwraps commands when a session id is provided", async () => {
    const commands = [{ id: "c1", session_id: "s1", type_: 1 }];
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: commands }),
    } as Response);

    const { result } = renderHook(() => useCommandsBySession("s1"), {
      wrapper: createQueryWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(commands);
  });
});

describe("useCreateCommand", () => {
  it("posts the payload and returns the created command", async () => {
    const created = { id: "c9", session_id: "s1", type_: 2 };
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ data: created }),
    } as Response);

    const { result } = renderHook(() => useCreateCommand(), { wrapper: createQueryWrapper() });

    const payload = { type_: 2, session_id: "s1" };
    await expect(result.current.mutateAsync(payload)).resolves.toEqual(created);

    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/commands/");
    expect(init).toMatchObject({ method: "POST" });
    expect(JSON.parse(String((init as RequestInit).body))).toEqual(payload);
  });

  it("rejects with an ApiError carrying the status code", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: "locked" }),
    } as Response);

    const { result } = renderHook(() => useCreateCommand(), { wrapper: createQueryWrapper() });

    await expect(result.current.mutateAsync({ type_: 2, session_id: "s1" })).rejects.toMatchObject({
      status: 409,
    });
    await expect(result.current.mutateAsync({ type_: 2, session_id: "s1" })).rejects.toBeInstanceOf(
      ApiError,
    );
  });
});

describe("useUpdateCommand", () => {
  it("patches the command by id", async () => {
    const updated = { id: "c1", session_id: "s1", type_: 1, status: "cancelled" };
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: updated }),
    } as Response);

    const { result } = renderHook(() => useUpdateCommand(), { wrapper: createQueryWrapper() });

    await expect(
      result.current.mutateAsync({ commandId: "c1", payload: { status: "cancelled" } }),
    ).resolves.toEqual(updated);

    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/commands/c1");
    expect(init).toMatchObject({ method: "PATCH" });
  });
});

describe("useDeleteCommand", () => {
  it("deletes the command by id and returns the message", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ message: "deleted" }),
    } as Response);

    const { result } = renderHook(() => useDeleteCommand(), { wrapper: createQueryWrapper() });

    await expect(result.current.mutateAsync("c1")).resolves.toEqual({ message: "deleted" });

    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/commands/c1");
    expect(init).toMatchObject({ method: "DELETE" });
  });
});
