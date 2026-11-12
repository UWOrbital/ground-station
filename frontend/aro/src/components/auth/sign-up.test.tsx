import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Signup from "./sign-up";
import { createQueryWrapper, jsonResponse } from "@/hooks/testUtils";
import toastService from "@/services/Toast.service";

vi.mock("@/services/Toast.service", () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

const QueryWrapper = createQueryWrapper();

/**
 * @brief Render the sign-up page inside the routes it can navigate to.
 * @return the testing-library render result.
 */
function renderSignup() {
  return render(
    <QueryWrapper>
      <MemoryRouter initialEntries={["/sign-up"]}>
        <Routes>
          <Route path="/sign-up" element={<Signup />} />
          <Route path="/verify/request" element={<div>Request Verification Page</div>} />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryWrapper>,
  );
}

/**
 * @brief Fill the required sign-up fields with valid values.
 * @param overrides values to type instead of the defaults.
 */
async function fillRequiredFields(overrides: Partial<Record<string, string>> = {}) {
  await userEvent.type(screen.getByLabelText(/First Name/), overrides.firstName ?? "Alice");
  await userEvent.type(screen.getByLabelText(/Call Sign/), overrides.callSign ?? "VA3ABC");
  await userEvent.type(screen.getByLabelText("Email"), overrides.email ?? "alice@example.com");
  await userEvent.type(screen.getByLabelText("Password"), overrides.password ?? "blah2bla");
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.mocked(toastService.success).mockClear();
  vi.mocked(toastService.error).mockClear();
});

describe("Signup", () => {
  it("registers with only the required fields and omits empty optionals", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(201, { id: "1" }));
    renderSignup();

    await fillRequiredFields();
    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/auth/register");

    const body = JSON.parse((init as RequestInit).body as string);
    expect(body.first_name).toBe("Alice");
    expect(body.call_sign).toBe("VA3ABC");
    expect(body.email).toBe("alice@example.com");
    expect(body.password).toBe("blah2bla");
    expect(body).not.toHaveProperty("last_name");
    expect(body).not.toHaveProperty("phone_number");
  });

  it("includes last name and phone number when provided", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(201, { id: "1" }));
    renderSignup();

    await fillRequiredFields();
    await userEvent.type(screen.getByLabelText(/Last Name/), "Smith");
    await userEvent.type(screen.getByLabelText(/Phone Number/), "+15195550123");
    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const body = JSON.parse((fetchSpy.mock.calls[0][1] as RequestInit).body as string);
    expect(body.last_name).toBe("Smith");
    expect(body.phone_number).toBe("+15195550123");
  });

  it("navigates to the verification page and toasts on success", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(201, { id: "1" }));
    renderSignup();

    await fillRequiredFields();
    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));

    expect(await screen.findByText("Request Verification Page")).toBeInTheDocument();
    expect(toastService.success).toHaveBeenCalled();
  });

  it("stays put and reports an error when registration is rejected", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(400, { detail: "REGISTER_USER_ALREADY_EXISTS" }),
    );
    renderSignup();

    await fillRequiredFields();
    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));

    await waitFor(() => expect(toastService.error).toHaveBeenCalled());
    expect(screen.queryByText("Request Verification Page")).not.toBeInTheDocument();
  });

  it("does not submit when a required field is empty", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(201, { id: "1" }));
    renderSignup();

    // Call sign deliberately left blank; the `required` attribute blocks submit.
    await userEvent.type(screen.getByLabelText(/First Name/), "Alice");
    await userEvent.type(screen.getByLabelText("Email"), "alice@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "blah2bla");
    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));

    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
