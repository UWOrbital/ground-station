import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { createQueryWrapper } from "@/hooks/testUtils";
import { API_BASE_URL } from "@/lib/apiClient";
import ForgotPassword from "./forgot-password";

function renderPage(): void {
  render(
    <MemoryRouter>
      <ForgotPassword />
    </MemoryRouter>,
    { wrapper: createQueryWrapper() },
  );
}

afterEach(() => vi.restoreAllMocks());

describe("ForgotPassword", () => {
  it("posts the email and confirms the reset link", async () => {
    const user = userEvent.setup();
    let resolveRequest!: (response: Response) => void;
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveRequest = resolve;
        }),
    );
    renderPage();

    expect(
      screen.getByText("Enter your email and we'll send you a link to reset your password."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveAttribute("placeholder", "name@example.com");

    await user.type(screen.getByLabelText("Email"), "ham@example.com");
    await user.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(screen.getByRole("button", { name: "Sending…" })).toBeDisabled();
    expect(screen.getByLabelText("Email")).toBeDisabled();
    expect(fetchSpy).toHaveBeenCalledExactlyOnceWith(`${API_BASE_URL}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "ham@example.com" }),
    });

    resolveRequest(new Response(null, { status: 202 }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      "We've sent a link to reset your password to ham@example.com.",
    );
    expect(screen.getByText(/The link will expire in 1 hour/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to login" })).toHaveAttribute("href", "/login");
  });

  it.each(["", "invalid-email"])("does not submit invalid input %j", async (email) => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    renderPage();
    if (email) await user.type(screen.getByLabelText("Email"), email);
    await user.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Email")).toBeInvalid();
  });

  it("shows an API error and allows a successful retry", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: { message: "Please try again later." } }), {
          status: 429,
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 202 }));
    renderPage();
    await user.type(screen.getByLabelText("Email"), "ham@example.com");
    await user.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Please try again later.");
    expect(screen.getByLabelText("Email")).toHaveValue("ham@example.com");
    await user.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(await screen.findByRole("status")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows a useful error when the network fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    renderPage();
    await user.type(screen.getByLabelText("Email"), "ham@example.com");
    await user.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to request password reset instructions. Please try again.",
    );
    expect(screen.getByRole("button", { name: "Send reset link" })).toBeEnabled();
  });

  it("resends the link to the submitted email", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(() => Promise.resolve(new Response(null, { status: 202 })));
    renderPage();
    await user.type(screen.getByLabelText("Email"), "ham@example.com");
    await user.click(screen.getByRole("button", { name: "Send reset link" }));
    await user.click(await screen.findByRole("button", { name: "Resend link" }));
    expect(fetchSpy).toHaveBeenCalledTimes(2);
    expect(fetchSpy).toHaveBeenLastCalledWith(
      `${API_BASE_URL}/auth/forgot-password`,
      expect.objectContaining({ body: JSON.stringify({ email: "ham@example.com" }) }),
    );
    expect(await screen.findByRole("status")).toHaveTextContent("ham@example.com");
  });
});
