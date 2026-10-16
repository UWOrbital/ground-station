import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./AuthContext";
import { accessTokenStore } from "@/lib/authToken";
import { parseOrThrow } from "@/lib/apiClient";
import { createQueryWrapper, jsonResponse, mockFetchByPath, tokenBody } from "@/hooks/testUtils";

const user = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "ham@example.com",
  is_active: true,
  is_superuser: false,
  is_verified: false,
  is_callsign_verified: false,
};

/**
 * @brief Test consumer rendering the auth state and exposing its actions as buttons.
 * @return tsx element describing the current auth state.
 */
function Probe() {
  const { user, isAuthenticated, isLoading, isUnavailable, recheck, login, logout } = useAuth();
  const status = isLoading
    ? "loading"
    : isUnavailable
      ? "unavailable"
      : isAuthenticated
        ? `signed in as ${user?.email}`
        : "signed out";
  return (
    <>
      <p>{status}</p>
      <button onClick={recheck}>recheck</button>
      <button onClick={() => login("ham@example.com", "pw").catch(() => {})}>login</button>
      <button onClick={() => logout().catch(() => {})}>logout</button>
    </>
  );
}

const renderProbe = () =>
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
    { wrapper: createQueryWrapper() },
  );

/**
 * @brief Render the Probe against a caller-owned QueryClient, so tests can inspect its cache.
 * @param queryClient the client to provide.
 * @return the render result.
 */
const renderProbeWith = (queryClient: QueryClient) =>
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Probe />
      </AuthProvider>
    </QueryClientProvider>,
  );

const signedInRoutes = () => ({
  "/auth/rotate_tokens": jsonResponse(200, tokenBody()),
  "/auth/get_current_user": jsonResponse(200, user),
});

beforeEach(() => {
  vi.restoreAllMocks();
  accessTokenStore.clear();
});

describe("AuthContext", () => {
  it("is loading, then signed in when the session is restored", async () => {
    mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, tokenBody()),
      "/auth/get_current_user": jsonResponse(200, user),
    });
    renderProbe();
    expect(screen.getByText("loading")).toBeInTheDocument();
    expect(await screen.findByText("signed in as ham@example.com")).toBeInTheDocument();
  });

  it("is signed out when there is no session", async () => {
    mockFetchByPath({ "/auth/rotate_tokens": jsonResponse(401) });
    renderProbe();
    expect(await screen.findByText("signed out")).toBeInTheDocument();
  });

  it("is unavailable, not signed out, when the first check can't reach the backend", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));
    renderProbe();
    expect(await screen.findByText("unavailable")).toBeInTheDocument();
  });

  it("recheck recovers from an unavailable backend", async () => {
    const rotate = vi
      .fn<() => Response>()
      .mockImplementationOnce(() => {
        throw new Error("network");
      })
      .mockReturnValue(jsonResponse(200, tokenBody()));
    mockFetchByPath({
      "/auth/rotate_tokens": rotate,
      "/auth/get_current_user": jsonResponse(200, user),
    });
    renderProbe();
    await screen.findByText("unavailable");

    await userEvent.click(screen.getByRole("button", { name: "recheck" }));

    expect(await screen.findByText("signed in as ham@example.com")).toBeInTheDocument();
  });

  it("recheck picks up a new session", async () => {
    const rotate = vi
      .fn<() => Response>()
      .mockReturnValueOnce(jsonResponse(401))
      .mockReturnValue(jsonResponse(200, tokenBody()));
    mockFetchByPath({
      "/auth/rotate_tokens": rotate,
      "/auth/get_current_user": jsonResponse(200, user),
    });
    renderProbe();
    await screen.findByText("signed out");

    await userEvent.click(screen.getByRole("button", { name: "recheck" }));

    expect(await screen.findByText("signed in as ham@example.com")).toBeInTheDocument();
  });

  it("login posts the credentials as a form and signs the user in", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/login": jsonResponse(200, tokenBody("logged-in")),
      "/auth/get_current_user": jsonResponse(200, user),
    });
    renderProbe();
    await screen.findByText("signed out");

    await userEvent.click(screen.getByRole("button", { name: "login" }));

    expect(await screen.findByText("signed in as ham@example.com")).toBeInTheDocument();
    expect(accessTokenStore.get()).toBe("logged-in");
    const loginCall = fetchSpy.mock.calls.find(([url]) => String(url).includes("/auth/login"));
    const body = (loginCall?.[1] as RequestInit).body as URLSearchParams;
    expect(body.get("username")).toBe("ham@example.com");
    expect(body.get("password")).toBe("pw");
  });

  it("stays signed out when login is rejected", async () => {
    mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/login": jsonResponse(401, {
        detail: { message: "Invalid credentials.", code: "invalid_credentials" },
      }),
    });
    renderProbe();
    await screen.findByText("signed out");

    await userEvent.click(screen.getByRole("button", { name: "login" }));

    expect(screen.getByText("signed out")).toBeInTheDocument();
    expect(accessTokenStore.get()).toBeNull();
  });

  it("logout revokes the session and clears other users' cached data", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(200, tokenBody()),
      "/auth/get_current_user": jsonResponse(200, user),
      "/auth/logout": jsonResponse(200, { message: "Logged out successfully." }),
    });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(["picture-requests", 100, 0], [{ id: "private" }]);
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Probe />
        </AuthProvider>
      </QueryClientProvider>,
    );
    await screen.findByText("signed in as ham@example.com");

    await userEvent.click(screen.getByRole("button", { name: "logout" }));

    expect(await screen.findByText("signed out")).toBeInTheDocument();
    expect(accessTokenStore.get()).toBeNull();
    expect(queryClient.getQueryData(["picture-requests", 100, 0])).toBeUndefined();
    const logoutCall = fetchSpy.mock.calls.find(([url]) => String(url).includes("/auth/logout"));
    expect((logoutCall?.[1] as RequestInit).method).toBe("POST");
  });

  it("signs out and clears cached user data when an API call gets a 401", async () => {
    mockFetchByPath(signedInRoutes());
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(["picture-requests", 100, 0], [{ id: "private" }]);
    renderProbeWith(queryClient);
    await screen.findByText("signed in as ham@example.com");

    await act(async () => {
      await parseOrThrow(jsonResponse(401)).catch(() => {});
    });

    expect(await screen.findByText("signed out")).toBeInTheDocument();
    expect(accessTokenStore.get()).toBeNull();
    expect(queryClient.getQueryData(["picture-requests", 100, 0])).toBeUndefined();
  });

  it("stops handling API 401s once unmounted", async () => {
    mockFetchByPath(signedInRoutes());
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { unmount } = renderProbeWith(queryClient);
    await screen.findByText("signed in as ham@example.com");
    unmount();
    queryClient.setQueryData(["picture-requests", 100, 0], [{ id: "kept" }]);

    await parseOrThrow(jsonResponse(401)).catch(() => {});

    expect(queryClient.getQueryData(["picture-requests", 100, 0])).toEqual([{ id: "kept" }]);
  });

  it("keeps the context value stable when only mutation state changes", async () => {
    mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/login": jsonResponse(401, { detail: "Invalid credentials." }),
    });
    const seen = new Set<ReturnType<typeof useAuth>>();
    /**
     * @brief Consumer recording every distinct context value it is rendered with.
     * @return nothing visible.
     */
    function ValueSpy() {
      seen.add(useAuth());
      return null;
    }
    render(
      <AuthProvider>
        <Probe />
        <ValueSpy />
      </AuthProvider>,
      { wrapper: createQueryWrapper() },
    );
    await screen.findByText("signed out");
    const settledCount = seen.size;

    // The rejected login moves the mutation through pending and error, re-rendering the provider.
    await userEvent.click(screen.getByRole("button", { name: "login" }));
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 20));
    });

    expect(seen.size).toBe(settledCount);
  });

  it("throws when used outside AuthProvider", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Probe />, { wrapper: createQueryWrapper() })).toThrow(
      "useAuth must be used within AuthProvider",
    );
  });
});
