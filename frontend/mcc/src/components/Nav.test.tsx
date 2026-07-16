import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import Nav from "./Nav";
import { AuthProvider } from "../contexts/AuthContext";
import { ThemeProvider } from "../contexts/ThemeContext";

describe("Nav", () => {
  it("renders logo", async () => {
    render(
      <AuthProvider>
        <ThemeProvider>
          <BrowserRouter>
            <Nav />
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByAltText("orbital logo")).toBeInTheDocument();
    });
  });

  it("renders navigation links", async () => {
    render(
      <AuthProvider>
        <ThemeProvider>
          <BrowserRouter>
            <Nav />
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
      expect(screen.getByText("Commands")).toBeInTheDocument();
      expect(screen.getByText("ARO Admin")).toBeInTheDocument();
      expect(screen.getByText("Live Sessions")).toBeInTheDocument();
      expect(screen.getByText("Login")).toBeInTheDocument();
    });
  });
});
