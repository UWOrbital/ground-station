import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import AROAdmin from "@/pages/AROAdmin";
import { useAroRequests } from "@/hooks/useAroRequests";

vi.mock("@/hooks/useAroRequests", () => ({ useAroRequests: vi.fn() }));

const hookReturns = (value: object) =>
  vi.mocked(useAroRequests).mockReturnValue(value as ReturnType<typeof useAroRequests>);

describe("ARO Admin Page", () => {
  it("shows a loading message while the requests are fetched", () => {
    hookReturns({ isLoading: true });
    render(<AROAdmin />);
    expect(screen.getByText("Loading requests...")).toBeInTheDocument();
  });

  it ("shows the error message when the fetch fails", () => {
    hookReturns({ isLoading: false, isError: true, error: new Error("No requests yet") });
    render(<AROAdmin />);
    expect(screen.getByText("No requests yet")).toBeInTheDocument();
  });

  it("renders the ARO requests in a table", () => {
    hookReturns({
      isLoading: false,
      isError: false,
      data: [
        { id: "r1", aro_id: "u1", latitude: 47.5, longitude: -122.3,
          created_on: "2026-01-01T00:00:00Z", status: "pending"
        },
      ],
    });
    render(<AROAdmin />);
    expect(screen.getByText("pending")).toBeInTheDocument();
    expect(screen.getByText("u1")).toBeInTheDocument();
  });
})
