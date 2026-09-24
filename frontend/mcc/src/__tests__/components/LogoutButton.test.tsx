import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LogoutButton from "@/components/LogoutButton";
import { API_BASE_URL } from "@/lib/apiClient";

describe("LogoutButton", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the user to the backend logout endpoint", async () => {
    vi.stubGlobal("location", { href: "" });
    render(<LogoutButton />);
    await userEvent.click(screen.getByRole("button", { name: "Logout" }));
    expect(window.location.href).toBe(`${API_BASE_URL}/auth/logout`);
  });
});
