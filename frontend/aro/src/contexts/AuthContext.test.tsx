import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./AuthContext";
import { clearAccessToken, getAccessToken } from "@/lib/authToken";
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
  const { user, isAuthenticated, isLoading, recheck, login, logout } = useAuth();
  return (
    <>
      <p>
        {isLoading ? "loading" : isAuthenticated ? `signed in as ${user?.email}` : "signed out"}
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

beforeEach(() => {
  vi.restoreAllMocks();
  clearAccessToken();
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
    expect(getAccessToken()).toBe("logged-in");
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
    expect(getAccessToken()).toBeNull();
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
    expect(getAccessToken()).toBeNull();
    expect(queryClient.getQueryData(["picture-requests", 100, 0])).toBeUndefined();
    const logoutCall = fetchSpy.mock.calls.find(([url]) => String(url).includes("/auth/logout"));
    expect((logoutCall?.[1] as RequestInit).method).toBe("POST");
  });

  it("throws when used outside AuthProvider", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Probe />, { wrapper: createQueryWrapper() })).toThrow(
      "useAuth must be used within AuthProvider",
    );
  });
});
