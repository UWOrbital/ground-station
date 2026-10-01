import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { focusManager } from "@tanstack/react-query";
import { useAuthStatus } from "./useAuthStatus";
import { ApiError } from "@/lib/apiClient";
import { accessTokenStore } from "@/lib/authToken";
import {
  calledUrls,
  createQueryWrapper,
  jsonResponse,
  mockFetchByPath,
  tokenBody,
} from "./testUtils";

const user = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "ham@example.com",
  is_active: true,
  is_superuser: false,
  is_verified: false,
  is_callsign_verified: true,
};

/**
 * @brief Render useAuthStatus and wait for it to settle.
 * @return the renderHook result.
 */
const renderSettled = async () => {
  const hook = renderHook(() => useAuthStatus(), { wrapper: createQueryWrapper() });
  await waitFor(() => expect(hook.result.current.isSuccess).toBe(true));
  return hook;
};

/**
 * @brief Render useAuthStatus and wait for it to fail.
 * @return the renderHook result.
 */
const renderErrored = async () => {
  const hook = renderHook(() => useAuthStatus(), { wrapper: createQueryWrapper() });
  await waitFor(() => expect(hook.result.current.isError).toBe(true));
  return hook;
};

beforeEach(() => {
  vi.restoreAllMocks();
  accessTokenStore.clear();
  focusManager.setFocused(undefined);
});

describe("useAuthStatus", () => {
  it("resolves to the user when a valid token is held", async () => {
    accessTokenStore.set("abc");
    const fetchSpy = mockFetchByPath({ "/auth/get_current_user": jsonResponse(200, user) });

    const { result } = await renderSettled();

    expect(result.current.data).toEqual(user);
    expect(calledUrls(fetchSpy)).toEqual([expect.stringContaining("/auth/get_current_user")]);
  });

  it("restores the session from the refresh cookie after a reload", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, tokenBody()),
      "/auth/get_current_user": jsonResponse(200, user),
    });

    const { result } = await renderSettled();

    expect(result.current.data).toEqual(user);
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("resolves to null without a user lookup when there is no session", async () => {
    const fetchSpy = mockFetchByPath({ "/auth/rotate_tokens": jsonResponse(401) });

    const { result } = await renderSettled();

    expect(result.current.data).toBeNull();
    expect(calledUrls(fetchSpy)).toEqual([expect.stringContaining("/auth/rotate_tokens")]);
  });

  it("resolves to null when the user lookup is rejected", async () => {
    accessTokenStore.set("abc");
    mockFetchByPath({
      "/auth/get_current_user": jsonResponse(401),
      "/auth/rotate_tokens": jsonResponse(401),
    });

    const { result } = await renderSettled();

    expect(result.current.data).toBeNull();
  });

  it("errors instead of signing out when the backend can't be reached", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));

    const { result } = await renderErrored();

    expect(result.current.data).toBeUndefined();
  });

  it("errors instead of signing out when the user lookup hits a server error", async () => {
    accessTokenStore.set("abc");
    mockFetchByPath({ "/auth/get_current_user": jsonResponse(500, { detail: "boom" }) });

    const { result } = await renderErrored();

    expect(result.current.error).toBeInstanceOf(ApiError);
    expect(result.current.data).toBeUndefined();
  });

  it("keeps the signed-in user when a later refetch fails", async () => {
    accessTokenStore.set("abc");
    const lookup = vi
      .fn<() => Response>()
      .mockReturnValueOnce(jsonResponse(200, user))
      .mockImplementation(() => {
        throw new Error("network");
      });
    mockFetchByPath({ "/auth/get_current_user": lookup });
    const { result } = await renderSettled();

    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(lookup).toHaveBeenCalledTimes(2);
    expect(result.current.data).toEqual(user);
  });

  it("does not re-check on window focus while the status is fresh", async () => {
    accessTokenStore.set("abc");
    const fetchSpy = mockFetchByPath({ "/auth/get_current_user": jsonResponse(200, user) });
    await renderSettled();

    await act(async () => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
      // Give a focus-triggered refetch the chance to fire before asserting it didn't.
      await new Promise((resolve) => setTimeout(resolve, 20));
    });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});
