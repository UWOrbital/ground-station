import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom";
import type { ReactNode } from "react";
import Nav from "./Nav";
import { AuthProvider } from "../contexts/AuthContext";
import { ThemeProvider } from "../contexts/ThemeContext";

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
      expect(screen.getByText("Live Sessions")).toBeInTheDocument();
      expect(screen.getByText("Login")).toBeInTheDocument();
    });
  });
});
