import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Login from "@/pages/Login";
import { API_BASE_URL } from "@/lib/apiClient";

describe("Login Page", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the user to the backend Keycloak login", async () => {
    vi.stubGlobal("location", { href: "" });
    render(<Login />);
    expect(screen.getByRole("heading", { name: "Login" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Sign in with Keycloak" }));
    expect(window.location.href).toBe(`${API_BASE_URL}/auth/login`);
  });
});
