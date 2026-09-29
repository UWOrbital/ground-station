import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { clearAccessToken } from "@/lib/authToken";
import { createQueryWrapper, jsonResponse, mockFetchByPath } from "@/hooks/testUtils";

/**
 * @brief Render the full App at a path with a signed-out backend.
 * @param path the initial route.
 */
const renderAppAt = (path: string) => {
  mockFetchByPath({ "/auth/rotate_tokens": jsonResponse(401) });
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
    { wrapper: createQueryWrapper() },
  );
};

beforeEach(() => {
  vi.restoreAllMocks();
  clearAccessToken();
});

describe("App", () => {
  it("renders the home page for signed-out users", async () => {
    renderAppAt("/");
    expect(await screen.findByText("Amateur Radio Operator")).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Login" })).toBeInTheDocument();
  });

  it("redirects signed-out users away from protected pages", async () => {
    renderAppAt("/new-request");
    expect(await screen.findByText("Login to your ARO Account")).toBeInTheDocument();
  });
});
