import { describe, it, expect, vi, beforeEach } from "vitest";
import { useState } from "react";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider, useMutationState } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./AuthContext";
import { accessTokenStore } from "@/lib/authToken";
import { shouldRetry } from "@/lib/apiClient";
import { usePictureRequests } from "@/hooks/usePictureRequests";
import {
  calledUrls,
  createQueryWrapper,
  jsonResponse,
  mockFetchByPath,
  tokenBody,
} from "@/hooks/testUtils";

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
  const { status, user, recheck, login, logout } = useAuth();
  return (
    <>
      <p>
        {status}
        {user && ` as ${user.email}`}
      </p>
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
 * @brief Test page loading the user's picture requests, like a real ARO page.
 * @return the query status once opened, or the button that opens the page.
 */
function Requests() {
  const [shown, setShown] = useState(false);
  return shown ? <RequestsStatus /> : <button onClick={() => setShown(true)}>open requests</button>;
}

/**
 * @brief Render the picture-requests query status.
 * @return tsx element showing the query status.
 */
function RequestsStatus() {
  const { status } = usePictureRequests();
  return <p>requests {status}</p>;
}

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
        <Requests />
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
    expect(await screen.findByText("signedIn as ham@example.com")).toBeInTheDocument();
  });

  it("is signed out when there is no session", async () => {
    mockFetchByPath({ "/auth/rotate_tokens": jsonResponse(401) });
    renderProbe();
    expect(await screen.findByText("signedOut")).toBeInTheDocument();
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

    expect(await screen.findByText("signedIn as ham@example.com")).toBeInTheDocument();
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
    await screen.findByText("signedOut");

    await userEvent.click(screen.getByRole("button", { name: "recheck" }));

    expect(await screen.findByText("signedIn as ham@example.com")).toBeInTheDocument();
  });

  it("login posts the credentials as a form and signs the user in", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/login": jsonResponse(200, tokenBody("logged-in")),
      "/auth/get_current_user": jsonResponse(200, user),
    });
    renderProbe();
    await screen.findByText("signedOut");

    await userEvent.click(screen.getByRole("button", { name: "login" }));

    expect(await screen.findByText("signedIn as ham@example.com")).toBeInTheDocument();
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
    await screen.findByText("signedOut");

    await userEvent.click(screen.getByRole("button", { name: "login" }));

    expect(screen.getByText("signedOut")).toBeInTheDocument();
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
    renderProbeWith(queryClient);
    await screen.findByText("signedIn as ham@example.com");

    await userEvent.click(screen.getByRole("button", { name: "logout" }));

    expect(await screen.findByText("signedOut")).toBeInTheDocument();
    expect(accessTokenStore.get()).toBeNull();
    expect(queryClient.getQueryData(["picture-requests", 100, 0])).toBeUndefined();
    const logoutCall = fetchSpy.mock.calls.find(([url]) => String(url).includes("/auth/logout"));
    expect((logoutCall?.[1] as RequestInit).method).toBe("POST");
  });

  it("signs out when a page's API call gets a 401, and the page shows the error", async () => {
    const fetchSpy = mockFetchByPath({
      ...signedInRoutes(),
      // The session is gone by the time the page loads: the refresh after its 401 fails too.
      "/auth/rotate_tokens": vi
        .fn<() => Response>()
        .mockReturnValueOnce(jsonResponse(200, tokenBody()))
        .mockReturnValue(jsonResponse(401)),
      "/requests/": jsonResponse(401),
    });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: shouldRetry } } });
    queryClient.setQueryData(["other-user-data"], { id: "private" });
    renderProbeWith(queryClient);
    await screen.findByText("signedIn as ham@example.com");

    await userEvent.click(screen.getByRole("button", { name: "open requests" }));

    expect(await screen.findByText("requests error")).toBeInTheDocument();
    expect(screen.getByText("signedOut")).toBeInTheDocument();
    expect(accessTokenStore.get()).toBeNull();
    expect(queryClient.getQueryData(["other-user-data"])).toBeUndefined();
    // Neither retried nor refetched once signed out.
    expect(calledUrls(fetchSpy).filter((url) => url.includes("/requests/"))).toHaveLength(1);
  });

  it("stays signed out when an auth check in flight during a 401 then succeeds", async () => {
    let answerUser!: () => void;
    const fetchSpy = mockFetchByPath({
      ...signedInRoutes(),
      // Held open, so the auth check is still in flight when the page's 401 arrives.
      "/auth/get_current_user": () =>
        new Promise((resolve) => (answerUser = () => resolve(jsonResponse(200, user)))),
      "/requests/": jsonResponse(401),
    });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    renderProbeWith(queryClient);
    await vi.waitFor(() =>
      expect(calledUrls(fetchSpy).some((url) => url.includes("/auth/get_current_user"))).toBe(true),
    );

    await userEvent.click(screen.getByRole("button", { name: "open requests" }));
    await screen.findByText("signedOut");
    await act(async () => {
      answerUser();
      // Let the late user response settle all the way into the cache.
      await new Promise((resolve) => setTimeout(resolve, 20));
    });

    expect(screen.getByText("signedOut")).toBeInTheDocument();
  });

  it("login drops data a previous user left in the cache", async () => {
    mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/login": jsonResponse(200, tokenBody("logged-in")),
      "/auth/get_current_user": jsonResponse(200, user),
    });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    renderProbeWith(queryClient);
    await screen.findByText("signedOut");
    queryClient.setQueryData(["picture-requests", 100, 0], [{ id: "previous user" }]);

    await userEvent.click(screen.getByRole("button", { name: "login" }));

    await screen.findByText("signedIn as ham@example.com");
    expect(queryClient.getQueryData(["picture-requests", 100, 0])).toBeUndefined();
  });

  it("keeps the context value stable when only mutation state changes", async () => {
    mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/login": jsonResponse(401, { detail: "Invalid credentials." }),
    });
    const seen = new Set<ReturnType<typeof useAuth>>();
    /**
     * @brief Consumer recording every distinct context value it is rendered with.
     * @return the login mutation's status, re-rendered in the same batch as the provider.
     */
    function ValueSpy() {
      seen.add(useAuth());
      const [loginStatus] = useMutationState({ select: (mutation) => mutation.state.status });
      return <p>login {loginStatus ?? "idle"}</p>;
    }
    render(
      <AuthProvider>
        <Probe />
        <ValueSpy />
      </AuthProvider>,
      { wrapper: createQueryWrapper() },
    );
    await screen.findByText("signedOut");
    const settledCount = seen.size;

    // The rejected login moves the mutation through pending and error, re-rendering the provider.
    await userEvent.click(screen.getByRole("button", { name: "login" }));
    await screen.findByText("login error");

    expect(seen.size).toBe(settledCount);
  });

  it("throws when used outside AuthProvider", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Probe />, { wrapper: createQueryWrapper() })).toThrow(
      "useAuth must be used within AuthProvider",
    );
  });
});
