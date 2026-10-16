import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiError, authFetch, authHeaders, errorMessage, refreshAccessToken } from "./apiClient";
import { accessTokenStore } from "./authToken";
import { calledUrls, jsonResponse, mockFetchByPath, tokenBody } from "@/hooks/testUtils";

const signIn = (token: string = "old-token") => accessTokenStore.set(token);

/**
 * @brief Read the Authorization header sent on the nth fetch call.
 * @param fetchSpy the fetch spy.
 * @param n index of the call to inspect.
 * @return the Authorization header value, if any.
 */
const authHeaderOf = (fetchSpy: { mock: { calls: unknown[][] } }, n: number) =>
  ((fetchSpy.mock.calls[n][1] as RequestInit).headers as Record<string, string>).Authorization;

beforeEach(() => {
  vi.restoreAllMocks();
  accessTokenStore.clear();
});

describe("authHeaders", () => {
  it("omits Authorization when signed out", () => {
    expect(authHeaders()).toEqual({ "Content-Type": "application/json" });
  });

  it("adds the bearer token when signed in", () => {
    signIn("abc");
    expect(authHeaders().Authorization).toBe("Bearer abc");
  });
});

describe("refreshAccessToken", () => {
  it("stores the rotated token on success", async () => {
    mockFetchByPath({ "/auth/rotate_tokens": jsonResponse(200, tokenBody("new-token")) });

    expect(await refreshAccessToken()).toBe(true);
    expect(accessTokenStore.get()).toBe("new-token");
  });

  it("clears the token when the refresh cookie is rejected", async () => {
    signIn();
    mockFetchByPath({ "/auth/rotate_tokens": jsonResponse(401) });

    expect(await refreshAccessToken()).toBe(false);
    expect(accessTokenStore.get()).toBeNull();
  });

  it("rejects without clearing the token when the network fails", async () => {
    signIn();
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));

    await expect(refreshAccessToken()).rejects.toThrow("network");
    expect(accessTokenStore.get()).toBe("old-token");
  });

  it("rejects without clearing the token on a server error", async () => {
    signIn();
    mockFetchByPath({ "/auth/rotate_tokens": jsonResponse(503, { detail: "down" }) });

    const err = await refreshAccessToken().catch((e: unknown) => e);

    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).status).toBe(503);
    expect(accessTokenStore.get()).toBe("old-token");
  });

  it("lets a new rotation start after a failed one", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("network"))
      .mockResolvedValueOnce(jsonResponse(200, tokenBody("new-token")));

    await expect(refreshAccessToken()).rejects.toThrow("network");
    expect(await refreshAccessToken()).toBe(true);
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("shares one rotation between concurrent callers", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, tokenBody("new-token")),
    });

    const results = await Promise.all([refreshAccessToken(), refreshAccessToken()]);

    expect(results).toEqual([true, true]);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("rotates again once the previous rotation has settled", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, tokenBody()),
    });

    await refreshAccessToken();
    await refreshAccessToken();

    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });
});

describe("authFetch", () => {
  it("sends the held token without refreshing", async () => {
    signIn("abc");
    const fetchSpy = mockFetchByPath({ "/thing": jsonResponse(200) });

    const res = await authFetch("http://api/thing");

    expect(res.status).toBe(200);
    expect(calledUrls(fetchSpy)).toEqual(["http://api/thing"]);
    expect(authHeaderOf(fetchSpy, 0)).toBe("Bearer abc");
  });

  it("restores the session from the refresh cookie when no token is held", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, tokenBody("restored")),
      "/thing": jsonResponse(200),
    });

    await authFetch("http://api/thing");

    expect(calledUrls(fetchSpy)).toEqual([
      expect.stringContaining("/auth/rotate_tokens"),
      "http://api/thing",
    ]);
    expect(authHeaderOf(fetchSpy, 1)).toBe("Bearer restored");
  });

  it("refreshes and retries once after a 401", async () => {
    signIn("stale");
    const thing = vi
      .fn<() => Response>()
      .mockReturnValueOnce(jsonResponse(401))
      .mockReturnValueOnce(jsonResponse(200));
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, tokenBody("fresh")),
      "/thing": thing,
    });

    const res = await authFetch("http://api/thing");

    expect(res.status).toBe(200);
    expect(fetchSpy).toHaveBeenCalledTimes(3);
    expect(authHeaderOf(fetchSpy, 2)).toBe("Bearer fresh");
  });

  it("keeps using a server-issued token even when the local clock is far ahead", async () => {
    // A client clock an hour fast sees the server's expires_at as already past.
    const expiredLocally = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, {
        ...tokenBody("fresh"),
        expires_at: expiredLocally,
      }),
      "/thing": jsonResponse(200),
    });

    await authFetch("http://api/thing");
    await authFetch("http://api/thing");

    expect(calledUrls(fetchSpy)).toEqual([
      expect.stringContaining("/auth/rotate_tokens"),
      "http://api/thing",
      "http://api/thing",
    ]);
    expect(authHeaderOf(fetchSpy, 1)).toBe("Bearer fresh");
    expect(authHeaderOf(fetchSpy, 2)).toBe("Bearer fresh");
  });

  it("reuses a token another request rotated while this one was in flight", async () => {
    signIn("stale");
    const thing = vi
      .fn<() => Response>()
      .mockImplementationOnce(() => {
        accessTokenStore.set("rotated-elsewhere");
        return jsonResponse(401);
      })
      .mockReturnValueOnce(jsonResponse(200));
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, tokenBody("unused")),
      "/thing": thing,
    });

    const res = await authFetch("http://api/thing");

    expect(res.status).toBe(200);
    expect(calledUrls(fetchSpy)).toEqual(["http://api/thing", "http://api/thing"]);
    expect(authHeaderOf(fetchSpy, 1)).toBe("Bearer rotated-elsewhere");
  });

  it("returns the 401 when the refresh also fails", async () => {
    signIn("stale");
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/thing": jsonResponse(401),
    });

    const res = await authFetch("http://api/thing");

    expect(res.status).toBe(401);
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("does not refresh twice when the upfront refresh already failed", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/thing": jsonResponse(401),
    });

    await authFetch("http://api/thing");

    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("rejects instead of sending a tokenless request when the refresh can't reach the server", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": () => {
        throw new Error("network");
      },
      "/thing": jsonResponse(200),
    });

    await expect(authFetch("http://api/thing")).rejects.toThrow("network");
    expect(calledUrls(fetchSpy)).toEqual([expect.stringContaining("/auth/rotate_tokens")]);
  });

  it("lets callers override headers", async () => {
    signIn("abc");
    const fetchSpy = mockFetchByPath({ "/thing": jsonResponse(200) });

    await authFetch("http://api/thing", { headers: { "Content-Type": "text/plain" } });

    const headers = (fetchSpy.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("text/plain");
    expect(headers.Authorization).toBe("Bearer abc");
  });
});

describe("errorMessage", () => {
  it("reads a plain string detail", () => {
    expect(errorMessage({ detail: "boom" }, 500)).toBe("boom");
  });

  it("reads the message of an ARO auth error detail", () => {
    expect(
      errorMessage(
        { detail: { message: "Invalid credentials.", code: "invalid_credentials" } },
        401,
      ),
    ).toBe("Invalid credentials.");
  });

  it("falls back to the status code", () => {
    expect(errorMessage({}, 502)).toBe("Request failed: 502");
    expect(errorMessage(null, 502)).toBe("Request failed: 502");
  });
});
