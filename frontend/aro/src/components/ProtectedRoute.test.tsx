import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";

vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));

/**
 * @brief Stand-in login page that shows where the user was redirected from.
 * @return tsx element naming the original path.
 */
function LoginPage() {
  const from = (useLocation().state as { from?: { pathname: string } } | null)?.from?.pathname;
  return <p>login page from {from}</p>;
}

const renderAt = (auth: { isAuthenticated: boolean; isLoading: boolean }) => {
  vi.mocked(useAuth).mockReturnValue({
    ...auth,
    user: null,
    recheck: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  });
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
};

describe("ProtectedRoute", () => {
  it("shows a loading state while auth is being checked", () => {
    renderAt({ isAuthenticated: false, isLoading: true });
    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("secret page")).not.toBeInTheDocument();
  });

  it("redirects signed-out users to login, remembering where they were going", () => {
    renderAt({ isAuthenticated: false, isLoading: false });
    expect(screen.getByText("login page from /secret")).toBeInTheDocument();
    expect(screen.queryByText("secret page")).not.toBeInTheDocument();
  });

  it("renders the page for signed-in users", () => {
    renderAt({ isAuthenticated: true, isLoading: false });
    expect(screen.getByText("secret page")).toBeInTheDocument();
  });
});
