import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom";
import type { ReactNode } from "react";
import Nav from "@/components/Nav";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";

/**
 * @brief Wrap Nav in the providers it depends on for rendering in tests.
 * @param children the subtree to wrap.
 * @return the children wrapped in query, auth, theme, and router providers.
 */
function renderWithProviders(children: ReactNode) {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider>
          <BrowserRouter>{children}</BrowserRouter>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

describe("Nav", () => {
  it("renders logo", async () => {
    renderWithProviders(<Nav />);

    await waitFor(() => {
      expect(screen.getByAltText("orbital logo")).toBeInTheDocument();
    });
  });

  it("renders navigation links", async () => {
    renderWithProviders(<Nav />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
      expect(screen.getByText("Commands")).toBeInTheDocument();
      expect(screen.getByText("ARO Admin")).toBeInTheDocument();
      expect(screen.getByText("Sessions")).toBeInTheDocument();
      expect(screen.getByText("Login")).toBeInTheDocument();
    });
  });

  it("swaps Login for Profile and Logout once signed in", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: true } as Response);
    renderWithProviders(<Nav />);

    expect(await screen.findByRole("link", { name: "Profile" })).toHaveAttribute(
      "href",
      "/profile",
    );
    expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Login" })).not.toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it("toggles between light and dark mode", async () => {
    renderWithProviders(<Nav />);
    const toggle = screen.getByRole("button", { name: "Toggle theme" });
    expect(toggle).toHaveAttribute("title", "Switch to dark mode");

    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute("title", "Switch to light mode");
  });
});
