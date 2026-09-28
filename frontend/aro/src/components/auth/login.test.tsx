import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Login from "./login";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError } from "@/lib/apiClient";
import toastService from "@/services/Toast.service";

vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));
vi.mock("@/services/Toast.service", () => ({ default: { error: vi.fn(), success: vi.fn() } }));

const login = vi.fn<(email: string, password: string) => Promise<void>>();

/**
 * @brief Render the login page, optionally as a redirect from a protected page.
 * @param from the protected path ProtectedRoute redirected from, if any.
 */
const renderLogin = (from?: string) => {
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    recheck: vi.fn(),
    login,
    logout: vi.fn(),
  });
  render(
    <MemoryRouter
      initialEntries={[{ pathname: "/login", state: from ? { from: { pathname: from } } : null }]}
    >
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<p>home page</p>} />
        <Route path="/new-request" element={<p>new request page</p>} />
      </Routes>
    </MemoryRouter>,
  );
};

/**
 * @brief Fill in and submit the login form.
 */
const submitForm = async () => {
  await userEvent.type(screen.getByLabelText("Email"), "ham@example.com");
  await userEvent.type(screen.getByLabelText("Password"), "hunter2");
  await userEvent.click(screen.getByRole("button", { name: "Login" }));
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Login", () => {
  it("logs in with the entered credentials and goes home", async () => {
    login.mockResolvedValue();
    renderLogin();

    await submitForm();

    expect(login).toHaveBeenCalledWith("ham@example.com", "hunter2");
    expect(await screen.findByText("home page")).toBeInTheDocument();
  });

  it("returns to the protected page the user was redirected from", async () => {
    login.mockResolvedValue();
    renderLogin("/new-request");

    await submitForm();

    expect(await screen.findByText("new request page")).toBeInTheDocument();
  });

  it("shows the backend error and stays on the page when login fails", async () => {
    login.mockRejectedValue(new ApiError(401, "Invalid credentials."));
    renderLogin();

    await submitForm();

    expect(toastService.error).toHaveBeenCalledWith("Invalid credentials.");
    expect(screen.getByRole("button", { name: "Login" })).toBeEnabled();
    expect(screen.queryByText("home page")).not.toBeInTheDocument();
  });

  it("shows a generic error for unexpected failures", async () => {
    login.mockRejectedValue(new Error("network"));
    renderLogin();

    await submitForm();

    expect(toastService.error).toHaveBeenCalledWith("Login failed. Please try again.");
  });
});
