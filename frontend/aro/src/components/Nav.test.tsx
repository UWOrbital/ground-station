import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import Nav from "./Nav";
import { useAuth, type AuthState } from "@/contexts/AuthContext";
import { fakeAuthState } from "@/hooks/testUtils";

vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));

/**
 * @brief Render Nav with a mocked auth state.
 * @param auth the auth fields the Nav should see.
 */
const renderNav = (auth: Partial<AuthState>) => {
  vi.mocked(useAuth).mockReturnValue(fakeAuthState(auth));
  render(
    <BrowserRouter>
      <Nav />
    </BrowserRouter>,
  );
};

describe("Nav", () => {
  it("renders logo", () => {
    renderNav({ isAuthenticated: false, isLoading: false });
    expect(screen.getByAltText("orbital-logo")).toBeInTheDocument();
  });

  it("renders public navigation links and Login when signed out", () => {
    renderNav({ isAuthenticated: false, isLoading: false });
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Requests")).toBeInTheDocument();
    expect(screen.queryByText("New")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Login" })).toHaveAttribute("href", "/login");
    expect(screen.queryByRole("link", { name: "Profile" })).not.toBeInTheDocument();
  });

  it("shows New and Profile instead of Login when signed in", () => {
    renderNav({ isAuthenticated: true, isLoading: false });
    expect(screen.getByRole("link", { name: "New" })).toHaveAttribute("href", "/new-request");
    expect(screen.getByRole("link", { name: "Profile" })).toHaveAttribute("href", "/profile");
    expect(screen.queryByRole("link", { name: "Login" })).not.toBeInTheDocument();
  });

  it("shows neither Login nor Profile while the auth check is in flight", () => {
    renderNav({ isAuthenticated: false, isLoading: true });
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Login" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Profile" })).not.toBeInTheDocument();
  });

  it("shows neither Login nor Profile when the backend can't be reached", () => {
    renderNav({ isAuthenticated: false, isUnavailable: true });
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Login" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Profile" })).not.toBeInTheDocument();
  });
});
