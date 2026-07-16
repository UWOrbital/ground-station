import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import Nav from "./Nav";
import { AuthProvider } from "../contexts/AuthContext";
import { ThemeProvider } from "../contexts/ThemeContext";

vi.mock("../utils/api/auth", () => ({
  checkAuth: vi.fn().mockResolvedValue(false),
}))

describe("Nav", () => {
  it("renders logo", () => {
    render(
      <AuthProvider>
        <ThemeProvider>
          <BrowserRouter>
            <Nav />
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>,
    );
    expect(screen.getByAltText("orbital logo")).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    render(
      <AuthProvider>
        <ThemeProvider>
          <BrowserRouter>
            <Nav />
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>,
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Commands")).toBeInTheDocument();
    expect(screen.getByText("ARO Admin")).toBeInTheDocument();
    expect(screen.getByText("Live Sessions")).toBeInTheDocument();
    expect(screen.getByText("Login")).toBeInTheDocument();
  });
});
