import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import Images from "@/pages/Images";
import { useLatestImage } from "@/hooks/useLatestImage";

vi.mock("@/hooks/useLatestImage", () => ({ useLatestImage: vi.fn() }));

const hookReturns = (value: object) =>
  vi.mocked(useLatestImage).mockReturnValue(value as ReturnType<typeof useLatestImage>);

describe("Images Page", () => {
  it("shows a loading message while the image is fetched", () => {
    hookReturns({ isLoading: true });
    render(<Images />);
    expect(screen.getByText("Loading image...")).toBeInTheDocument();
  });

  it("shows the error message when the fetch fails", () => {
    hookReturns({ isLoading: false, isError: true, error: new Error("No images yet") });
    render(<Images />);
    expect(screen.getByText("No images yet")).toBeInTheDocument();
  });

  it("renders the latest image from its base64 data", () => {
    hookReturns({ isLoading: false, isError: false, data: { data: "aGVsbG8=" } });
    render(<Images />);
    expect(screen.getByRole("heading", { name: "Latest Satellite Image" })).toBeInTheDocument();
    expect(screen.getByAltText("Latest satellite downlink")).toHaveAttribute(
      "src",
      "data:image/jpeg;base64,aGVsbG8=",
    );
  });
});
