import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider, useTheme } from "@/contexts/ThemeContext";

function Probe() {
  const { theme, toggleTheme } = useTheme();
  return <button onClick={toggleTheme}>{theme}</button>;
}

const renderProbe = () =>
  render(
    <ThemeProvider>
      <Probe />
    </ThemeProvider>,
  );

describe("ThemeContext", () => {
  beforeEach(() => {
    vi.mocked(localStorage.getItem).mockReset();
    vi.mocked(localStorage.setItem).mockReset();
    document.documentElement.classList.remove("dark");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("defaults to light when nothing is stored and the system prefers light", () => {
    renderProbe();
    expect(screen.getByRole("button")).toHaveTextContent("light");
    expect(document.documentElement).not.toHaveClass("dark");
  });

  it("uses the stored theme over the system preference", () => {
    vi.mocked(localStorage.getItem).mockReturnValue("dark");
    renderProbe();
    expect(screen.getByRole("button")).toHaveTextContent("dark");
    expect(document.documentElement).toHaveClass("dark");
  });

  it("falls back to the system dark preference", () => {
    vi.spyOn(window, "matchMedia").mockReturnValue({ matches: true } as MediaQueryList);
    renderProbe();
    expect(screen.getByRole("button")).toHaveTextContent("dark");
  });

  it("toggles the theme, the root class, and the stored value", async () => {
    const user = userEvent.setup();
    renderProbe();

    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("button")).toHaveTextContent("dark");
    expect(document.documentElement).toHaveClass("dark");
    expect(localStorage.setItem).toHaveBeenLastCalledWith("theme", "dark");

    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("button")).toHaveTextContent("light");
    expect(document.documentElement).not.toHaveClass("dark");
    expect(localStorage.setItem).toHaveBeenLastCalledWith("theme", "light");
  });

  it("throws when used outside ThemeProvider", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Probe />)).toThrow("useTheme must be used within ThemeProvider");
  });
});
