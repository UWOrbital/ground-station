import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PageNotFound from "@/components/PageNotFound";

describe("PageNotFound", () => {
  it("explains the page is missing and links back home", () => {
    render(
      <MemoryRouter>
        <PageNotFound />
      </MemoryRouter>,
    );
    expect(screen.getByText(/lost in space/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "homepage" })).toHaveAttribute("href", "/");
  });
});
