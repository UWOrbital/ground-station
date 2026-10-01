import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import { useAuth, type AuthState } from "@/contexts/AuthContext";
import { fakeAuthState } from "@/hooks/testUtils";

vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));

/**
 * @brief Stand-in login page that shows where the user was redirected from.
 * @return tsx element naming the original path.
 */
function LoginPage() {
  const from = (useLocation().state as { from?: { pathname: string } } | null)?.from?.pathname;
  return <p>login page from {from}</p>;
}

/**
 * @brief Render a protected /secret page with a mocked auth state.
 * @param auth the auth fields the route should see.
 * @return the mocked auth state, for asserting on its actions.
 */
const renderAt = (auth: Partial<AuthState>) => {
  const state = fakeAuthState(auth);
  vi.mocked(useAuth).mockReturnValue(state);
  render(
    <MemoryRouter initialEntries={["/secret"]}>
      <Routes>
        <Route
          path="/secret"
          element={
            <ProtectedRoute>
              <p>secret page</p>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </MemoryRouter>,
  );
  return state;
};

describe("ProtectedRoute", () => {
  it("shows a loading state while auth is being checked", () => {
    renderAt({ isLoading: true });
    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("secret page")).not.toBeInTheDocument();
  });

  it("offers a retry instead of redirecting when the backend can't be reached", async () => {
    const state = renderAt({ isUnavailable: true });
    expect(screen.getByText(/can't reach the ARO server/i)).toBeInTheDocument();
    expect(screen.queryByText(/login page/)).not.toBeInTheDocument();
    expect(screen.queryByText("secret page")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(state.recheck).toHaveBeenCalledTimes(1);
  });

  it("redirects signed-out users to login, remembering where they were going", () => {
    renderAt({ isAuthenticated: false });
    expect(screen.getByText("login page from /secret")).toBeInTheDocument();
    expect(screen.queryByText("secret page")).not.toBeInTheDocument();
  });

  it("renders the page for signed-in users", () => {
    renderAt({ isAuthenticated: true });
    expect(screen.getByText("secret page")).toBeInTheDocument();
  });
});
