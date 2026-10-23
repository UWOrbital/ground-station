import { describe, it, expect, vi, beforeEach } from "vitest";
import { createElement, type ReactNode } from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { onlineManager, QueryClient, QueryClientProvider } from "@tanstack/react-query";
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

  it("drops the refreshed token when the user lookup still rejects it", async () => {
    mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, tokenBody("inactive-user-token")),
      "/auth/get_current_user": jsonResponse(401),
    });

    const { result } = await renderSettled();

    expect(result.current.data).toBeNull();
    expect(accessTokenStore.get()).toBeNull();
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

  it("keeps a resolved status fresh, so window refocus doesn't re-check it", async () => {
    accessTokenStore.set("abc");
    mockFetchByPath({ "/auth/get_current_user": jsonResponse(200, user) });

    const { result } = await renderSettled();

    expect(result.current.isStale).toBe(false);
  });

  it("fails after one attempt even when the app's client retries queries", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));
    // App defaults (retry: 3), unlike createQueryWrapper.
    const queryClient = new QueryClient();
    const wrapper = ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children);

    const { result } = renderHook(() => useAuthStatus(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    queryClient.clear();
  });

  it("errors instead of pausing while the browser is offline", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    onlineManager.setOnline(false);
    try {
      const { result } = await renderErrored();
      expect(result.current.data).toBeUndefined();
    } finally {
      onlineManager.setOnline(true);
    }
  });
});
