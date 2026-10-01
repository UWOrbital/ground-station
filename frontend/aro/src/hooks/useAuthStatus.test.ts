import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useAuthStatus } from "./useAuthStatus";
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

  it("resolves to null when fetch rejects", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));

    const { result } = await renderSettled();

    expect(result.current.data).toBeNull();
  });
});
