import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { accessTokenStore } from "@/lib/authToken";
import { createQueryWrapper, jsonResponse, mockFetchByPath, tokenBody } from "@/hooks/testUtils";

const signedOut = { "/auth/rotate_tokens": jsonResponse(401) };

const signedIn = {
  "/auth/rotate_tokens": jsonResponse(200, tokenBody()),
  "/auth/get_current_user": jsonResponse(200, {
    id: "11111111-1111-1111-1111-111111111111",
    email: "ham@example.com",
    is_active: true,
    is_superuser: false,
    is_verified: true,
    is_callsign_verified: true,
  }),
};

/**
 * @brief Render the full App at a path against a mocked backend.
 * @param path the initial route.
 * @param backend fetch responses by URL substring; defaults to a signed-out backend.
 */
const renderAppAt = (path: string, backend: Record<string, Response> = signedOut) => {
  mockFetchByPath(backend);
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
    { wrapper: createQueryWrapper() },
  );
};

beforeEach(() => {
  vi.restoreAllMocks();
  accessTokenStore.clear();
});

describe("App", () => {
  it("opens password recovery directly by its route", async () => {
    renderAppAt("/forgot-password");
    expect(await screen.findByRole("heading", { name: "Reset your password" })).toBeInTheDocument();
  });

  it("navigates from login to password recovery and back", async () => {
    const user = userEvent.setup();
    renderAppAt("/login");
    const link = await screen.findByRole("link", { name: "Forgot Your Password?" });
    expect(link).toHaveAttribute("href", "/forgot-password");
    await user.click(link);
    expect(await screen.findByRole("heading", { name: "Reset your password" })).toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: "Back to login" }));
    expect(
      await screen.findByRole("heading", { name: "Login to your ARO Account" }),
    ).toBeInTheDocument();
  });

  it("renders the home page for signed-out users", async () => {
    renderAppAt("/");
    expect(await screen.findByText("Amateur Radio Operator")).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Login" })).toBeInTheDocument();
  });

  it("redirects signed-out users away from protected pages", async () => {
    renderAppAt("/new-request");
    expect(await screen.findByText("Login to your ARO Account")).toBeInTheDocument();
  });

  it("lets signed-in users into protected pages and shows their nav links", async () => {
    renderAppAt("/profile/settings", signedIn);
    expect(await screen.findByLabelText("Callsign")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Profile" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "New" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Login" })).not.toBeInTheDocument();
  });

  it("sends signed-in users away from the login page", async () => {
    renderAppAt("/login", signedIn);
    expect(await screen.findByText("Amateur Radio Operator")).toBeInTheDocument();
    expect(screen.queryByText("Login to your ARO Account")).not.toBeInTheDocument();
  });

  it("offers a retry instead of the login page when the backend is down", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));
    render(
      <MemoryRouter initialEntries={["/profile/settings"]}>
        <App />
      </MemoryRouter>,
      { wrapper: createQueryWrapper() },
    );
    expect(await screen.findByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.queryByText("Login to your ARO Account")).not.toBeInTheDocument();
  });
});
