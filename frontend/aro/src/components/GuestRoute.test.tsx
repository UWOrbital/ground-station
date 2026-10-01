import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation, type InitialEntry } from "react-router-dom";
import GuestRoute from "./GuestRoute";
import ProtectedRoute from "./ProtectedRoute";
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
        <Route element={<GuestRoute />}>
          <Route path="/login" element={<p>login form</p>} />
        </Route>
        <Route path="*" element={<Landing />} />
      </Routes>
    </MemoryRouter>,
  );
};

describe("GuestRoute", () => {
  it("shows a loading state while auth is being checked", () => {
    renderLogin({ status: "loading" });
    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("login form")).not.toBeInTheDocument();
  });

  it("renders the page for signed-out users", () => {
    renderLogin({ status: "signedOut" });
    expect(screen.getByText("login form")).toBeInTheDocument();
  });

  it("sends signed-in users home when they weren't heading anywhere", () => {
    renderLogin({ status: "signedIn" });
    expect(screen.getByText("landed on /")).toBeInTheDocument();
  });

  it("sends signed-in users back to the page they were heading for", () => {
    renderLogin(
      { status: "signedIn" },
      {
        pathname: "/login",
        state: { from: { pathname: "/profile/gallery", search: "?page=2", hash: "#top" } },
      },
    );
    expect(screen.getByText("landed on /profile/gallery?page=2#top")).toBeInTheDocument();
  });

  it("returns users who sign in on the login page to the protected page they tried", () => {
    vi.mocked(useAuth).mockReturnValue(fakeAuthState({ status: "signedOut" }));
    // A fresh element per render, so React re-renders the guards with the new auth state.
    const app = () => (
      <MemoryRouter initialEntries={["/profile/gallery?page=2#top"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/profile/gallery" element={<Landing />} />
          </Route>
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<p>login form</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    const { rerender } = render(app());
    expect(screen.getByText("login form")).toBeInTheDocument();

    vi.mocked(useAuth).mockReturnValue(fakeAuthState({ status: "signedIn" }));
    rerender(app());

    expect(screen.getByText("landed on /profile/gallery?page=2#top")).toBeInTheDocument();
  });
});
