import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Login from "./login";
import { AuthProvider } from "@/contexts/AuthContext";
import { createQueryWrapper, jsonResponse, tokenBody, mockFetchByPath } from "@/hooks/testUtils";
import toastService from "@/services/Toast.service";

vi.mock("@/services/Toast.service", () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

const QueryWrapper = createQueryWrapper();

/**
 * @brief Render the login page inside the AuthProvider and the routes it navigates to.
 * @return the testing-library render result.
 */
function renderLogin() {
  return render(
    <QueryWrapper>
      <AuthProvider>
        <MemoryRouter initialEntries={["/login"]}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<div>Home Page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryWrapper>,
  );
}

/**
 * @brief Type valid credentials into the login form.
 */
async function fillCredentials() {
  await userEvent.type(screen.getByLabelText("Email"), "alice@example.com");
  await userEvent.type(screen.getByLabelText("Password"), "blah2bla");
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.mocked(toastService.success).mockClear();
  vi.mocked(toastService.error).mockClear();
});

describe("Login", () => {
  it("posts the typed credentials to the login endpoint", async () => {
    // AuthProvider mounts useAuthStatus, which tries to restore a session
    // first; answer rotate_tokens with a 401 so it resolves to "logged out".
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/get_current_user": jsonResponse(401),
      "/auth/login": jsonResponse(200, tokenBody()),
    });
    renderLogin();

    await fillCredentials();
    await userEvent.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() =>
      expect(fetchSpy.mock.calls.some((c) => String(c[0]).includes("/auth/login"))).toBe(true),
    );
    const loginCall = fetchSpy.mock.calls.find((c) => String(c[0]).includes("/auth/login"))!;
    const body = (loginCall[1] as RequestInit).body as URLSearchParams;
    // The backend expects OAuth2PasswordRequestForm, so email is sent as `username`.
    expect(body.get("username")).toBe("alice@example.com");
    expect(body.get("password")).toBe("blah2bla");
  });

  it("navigates home and toasts on a successful login", async () => {
    mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/get_current_user": jsonResponse(401),
      "/auth/login": jsonResponse(200, tokenBody()),
    });
    renderLogin();

    await fillCredentials();
    await userEvent.click(screen.getByRole("button", { name: "Login" }));

    expect(await screen.findByText("Home Page")).toBeInTheDocument();
    expect(toastService.success).toHaveBeenCalled();
  });

  it("stays on the page and reports an error on bad credentials", async () => {
    mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/get_current_user": jsonResponse(401),
      "/auth/login": jsonResponse(401, { detail: { message: "Invalid credentials.", code: "invalid_credentials" } }),
    });
    renderLogin();

    await fillCredentials();
    await userEvent.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => expect(toastService.error).toHaveBeenCalled());
    expect(screen.queryByText("Home Page")).not.toBeInTheDocument();
  });

  it("does not submit when a field is empty", async () => {
    const fetchSpy = mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/auth/get_current_user": jsonResponse(401),
      "/auth/login": jsonResponse(200, tokenBody()),
    });
    renderLogin();

    // Password left blank; the `required` attribute blocks submit.
    await userEvent.type(screen.getByLabelText("Email"), "alice@example.com");
    await userEvent.click(screen.getByRole("button", { name: "Login" }));

    expect(fetchSpy.mock.calls.some((c) => String(c[0]).includes("/auth/login"))).toBe(false);
  });
});
