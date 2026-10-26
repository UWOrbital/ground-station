import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Verify from "./verify";
import RequestVerification from "./request-verification";
import { createQueryWrapper } from "@/hooks/testUtils";

const okResponse = { ok: true, status: 202, json: async () => ({}) } as Response;

const QueryWrapper = createQueryWrapper();

/**
 * @brief Render an auth page inside the routes the app actually serves.
 * @param element the page under test
 * @param mountPath the route the page is served at
 * @param route the URL the browser starts on, query string included
 */
function renderAt(element: React.ReactElement, mountPath: string, route: string) {
  return render(
    <QueryWrapper>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path={mountPath} element={element} />
          {mountPath !== "/verify" && <Route path="/verify" element={<div>Code Entry Page</div>} />}
          {mountPath !== "/verify/request" && (
            <Route path="/verify/request" element={<div>Request Verification Page</div>} />
          )}
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryWrapper>,
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("RequestVerification", () => {
  it("requests a code for the typed email and moves to the code entry page", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(okResponse);
    renderAt(<RequestVerification />, "/verify/request", "/verify/request");

    await userEvent.type(screen.getByLabelText("Email"), "aro@example.com");
    await userEvent.click(screen.getByRole("button", { name: "Send Verification Code" }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/auth/request-verify-token");
    expect((init as RequestInit).body).toBe(JSON.stringify({ email: "aro@example.com" }));
    expect(await screen.findByText("Code Entry Page")).toBeInTheDocument();
  });
});

describe("Verify", () => {
  it("submits the code that the emailed link carried", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: "1", email: "aro@example.com", is_verified: true }),
    } as Response);
    renderAt(<Verify />, "/verify", "/verify?token=emailed-token&email=aro%40example.com");

    expect(screen.getByLabelText("OTP Verification Code")).toHaveValue("emailed-token");
    await userEvent.click(screen.getByRole("button", { name: "Confirm Code" }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/auth/verify");
    expect((init as RequestInit).body).toBe(JSON.stringify({ token: "emailed-token" }));
    expect(await screen.findByText("Login Page")).toBeInTheDocument();
  });

  it("stays put and reports a rejected code", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: "VERIFY_USER_BAD_TOKEN" }),
    } as Response);
    renderAt(<Verify />, "/verify", "/verify?email=aro%40example.com");

    await userEvent.type(screen.getByLabelText("OTP Verification Code"), "stale-token");
    await userEvent.click(screen.getByRole("button", { name: "Confirm Code" }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    expect(String(fetchSpy.mock.calls[0][0])).toContain("/auth/verify");
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
  });

  it("resends the code to the email on the url", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(okResponse);
    renderAt(<Verify />, "/verify", "/verify?email=aro%40example.com");

    await userEvent.click(screen.getByRole("button", { name: "Resend Code" }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/auth/request-verify-token");
    expect((init as RequestInit).body).toBe(JSON.stringify({ email: "aro@example.com" }));
  });

  it("asks for the email when resending without one on the url", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(okResponse);
    renderAt(<Verify />, "/verify", "/verify");

    await userEvent.click(screen.getByRole("button", { name: "Resend Code" }));

    expect(await screen.findByText("Request Verification Page")).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
