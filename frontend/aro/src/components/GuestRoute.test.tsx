import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation, type InitialEntry } from "react-router-dom";
import GuestRoute from "./GuestRoute";
import { useAuth, type AuthState } from "@/contexts/AuthContext";
import { fakeAuthState } from "@/hooks/testUtils";

vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));

/**
 * @brief Stand-in page that shows the URL it was reached at.
 * @return tsx element naming the current path, search and hash.
 */
function Landing() {
  const { pathname, search, hash } = useLocation();
  return <p>landed on {`${pathname}${search}${hash}`}</p>;
}

/**
 * @brief Render a guest-only /login page with a mocked auth state.
 * @param auth the auth fields the route should see.
 * @param entry the initial history entry (path plus optional state).
 */
const renderLogin = (auth: Partial<AuthState>, entry: InitialEntry = "/login") => {
  vi.mocked(useAuth).mockReturnValue(fakeAuthState(auth));
  render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route
          path="/login"
          element={
            <GuestRoute>
              <p>login form</p>
            </GuestRoute>
          }
        />
        <Route path="*" element={<Landing />} />
      </Routes>
    </MemoryRouter>,
  );
};

describe("GuestRoute", () => {
  it("shows a loading state while auth is being checked", () => {
    renderLogin({ isLoading: true });
    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("login form")).not.toBeInTheDocument();
  });

  it("renders the page for signed-out users", () => {
    renderLogin({ isAuthenticated: false });
    expect(screen.getByText("login form")).toBeInTheDocument();
  });

  it("sends signed-in users home when they weren't heading anywhere", () => {
    renderLogin({ isAuthenticated: true });
    expect(screen.getByText("landed on /")).toBeInTheDocument();
  });

  it("sends signed-in users back to the page they were heading for", () => {
    renderLogin(
      { isAuthenticated: true },
      {
        pathname: "/login",
        state: { from: { pathname: "/profile/gallery", search: "?page=2", hash: "#top" } },
      },
    );
    expect(screen.getByText("landed on /profile/gallery?page=2#top")).toBeInTheDocument();
  });

  it("handles a `from` that only has a pathname", () => {
    renderLogin(
      { isAuthenticated: true },
      { pathname: "/login", state: { from: { pathname: "/new-request" } } },
    );
    expect(screen.getByText("landed on /new-request")).toBeInTheDocument();
  });
});
