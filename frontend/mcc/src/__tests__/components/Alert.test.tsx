import { describe, it, expect, vi, afterEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import CustomAlert from "@/components/Alert";

describe("CustomAlert", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows a green success alert with its title and description", () => {
    render(<CustomAlert title="Saved" description="All good" />);
    expect(screen.getByRole("alert")).toHaveClass("text-green-500");
    expect(screen.getByText("Saved")).toBeInTheDocument();
    expect(screen.getByText("All good")).toBeInTheDocument();
  });

  it("shows a red destructive alert and omits an empty description", () => {
    render(<CustomAlert destructive title="Failed" />);
    expect(screen.getByRole("alert")).toHaveClass("text-red-500");
    expect(screen.getByRole("alert")).toHaveTextContent(/^Failed$/);
  });

  it("stays visible when no timeout is given", () => {
    vi.useFakeTimers();
    render(<CustomAlert title="Sticky" />);
    act(() => vi.advanceTimersByTime(60_000));
    expect(screen.getByText("Sticky")).toBeInTheDocument();
  });

  it("disappears once its timeout elapses", () => {
    vi.useFakeTimers();
    render(<CustomAlert title="Brief" timeout={7000} />);

    act(() => vi.advanceTimersByTime(6999));
    expect(screen.getByText("Brief")).toBeInTheDocument();

    act(() => vi.advanceTimersByTime(1));
    expect(screen.queryByText("Brief")).not.toBeInTheDocument();
  });
});
