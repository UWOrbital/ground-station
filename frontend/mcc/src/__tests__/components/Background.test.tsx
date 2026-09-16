import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Background from "@/components/Background";
import { ThemeProvider } from "@/contexts/ThemeContext";

describe("Background", () => {
  it("renders background image", () => {
    render(
      <ThemeProvider>
        <Background />
      </ThemeProvider>,
    );
    expect(screen.getByAltText("background-image")).toBeInTheDocument();
  });

  it("has correct CSS classes", () => {
    render(
      <ThemeProvider>
        <Background />
      </ThemeProvider>,
    );
    const image = screen.getByAltText("background-image");
    // In light mode (default), opacity should be slightly higher for visibility
    expect(image).toHaveClass("opacity-30");
  });

  it("dims the image more in dark mode", () => {
    vi.mocked(localStorage.getItem).mockReturnValueOnce("dark");
    render(
      <ThemeProvider>
        <Background />
      </ThemeProvider>,
    );
    expect(screen.getByAltText("background-image")).toHaveClass("opacity-40");
  });
});
