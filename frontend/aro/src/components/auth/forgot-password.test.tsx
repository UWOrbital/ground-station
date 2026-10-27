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
  it("posts the email and accepts an empty 202 response with a neutral confirmation", async () => {
    const user = userEvent.setup();
    let resolveRequest!: (response: Response) => void;
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveRequest = resolve;
        }),
    );
    renderPage();

    await user.type(screen.getByLabelText("Email"), "ham@example.com");
    await user.click(screen.getByRole("button", { name: "Send Reset Instructions" }));
    expect(screen.getByRole("button", { name: "Sending…" })).toBeDisabled();
    expect(screen.getByLabelText("Email")).toBeDisabled();
    expect(fetchSpy).toHaveBeenCalledExactlyOnceWith(`${API_BASE_URL}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "ham@example.com" }),
    });

    resolveRequest(new Response(null, { status: 202 }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      "If an account exists for that email",
    );
    expect(screen.getByRole("link", { name: "Back to Login" })).toHaveAttribute("href", "/login");
  });

  it.each(["", "invalid-email"])("does not submit invalid input %j", async (email) => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    renderPage();
    if (email) await user.type(screen.getByLabelText("Email"), email);
    await user.click(screen.getByRole("button", { name: "Send Reset Instructions" }));
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
    await user.click(screen.getByRole("button", { name: "Send Reset Instructions" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Please try again later.");
    expect(screen.getByLabelText("Email")).toHaveValue("ham@example.com");
    await user.click(screen.getByRole("button", { name: "Send Reset Instructions" }));
    expect(await screen.findByRole("status")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows a useful error when the network fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    renderPage();
    await user.type(screen.getByLabelText("Email"), "ham@example.com");
    await user.click(screen.getByRole("button", { name: "Send Reset Instructions" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to request password reset instructions. Please try again.",
    );
    expect(screen.getByRole("button", { name: "Send Reset Instructions" })).toBeEnabled();
  });
});
