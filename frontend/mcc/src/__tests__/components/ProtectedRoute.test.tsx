import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";

vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));

const renderAt = (auth: { isAuthenticated: boolean; isLoading: boolean }) => {
  vi.mocked(useAuth).mockReturnValue({ ...auth, recheck: vi.fn() });
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
        <Route path="/login" element={<p>login page</p>} />
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

  it("redirects signed-out users to login", () => {
    renderAt({ isAuthenticated: false, isLoading: false });
    expect(screen.getByText("login page")).toBeInTheDocument();
    expect(screen.queryByText("secret page")).not.toBeInTheDocument();
  });

  it("renders the page for signed-in users", () => {
    renderAt({ isAuthenticated: true, isLoading: false });
    expect(screen.getByText("secret page")).toBeInTheDocument();
  });
});
