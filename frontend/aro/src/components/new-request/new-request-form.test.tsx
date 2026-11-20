import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createQueryWrapper, jsonResponse, mockFetchByPath } from "@/hooks/testUtils";
import { accessTokenStore } from "@/lib/authToken";
import NewRequestForm from "./new-request-form";

const toast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }));
vi.mock("@/services/Toast.service", () => ({ default: toast }));
// Leaflet needs real layout/canvas APIs that jsdom lacks; the map isn't under test here.
vi.mock("./map-view", () => ({ default: () => null }));

const CREATED = {
  id: "11111111-1111-1111-1111-111111111111",
  aro_id: "22222222-2222-2222-2222-222222222222",
  latitude: "43.472",
  longitude: "-80.545",
  created_on: "2026-01-01T00:00:00Z",
  request_sent_to_obc_on: null,
  pic_taken_on: null,
  pic_transmitted_on: null,
  delete_deadline: "2026-01-02T00:00:00Z",
  packet_id: null,
  status: "pending",
  operations: {},
};

/**
 * @brief Make the browser report a fixed, high-precision location.
 * @param latitude reported latitude.
 * @param longitude reported longitude.
 */
function mockGeolocation(latitude: number, longitude: number): void {
  Object.defineProperty(navigator, "geolocation", {
    configurable: true,
    value: {
      getCurrentPosition: (onSuccess: PositionCallback) =>
        onSuccess({ coords: { latitude, longitude } } as GeolocationPosition),
    },
  });
}

/**
 * @brief Render the form and wait for the location lookup to fill it in.
 * @return the latitude and longitude inputs.
 */
async function renderForm() {
  render(<NewRequestForm />, { wrapper: createQueryWrapper() });
  const latitude = await screen.findByPlaceholderText("Enter latitude");
  const longitude = screen.getByPlaceholderText("Enter longitude");
  return { latitude, longitude };
}

/**
 * @brief Collect the bodies of the POST calls a fetch spy received.
 * @param fetchSpy the spy to inspect.
 * @return the parsed JSON body of every POST.
 */
function postedBodies(fetchSpy: { mock: { calls: unknown[][] } }): unknown[] {
  return fetchSpy.mock.calls
    .map((call) => (call[1] ?? {}) as RequestInit)
    .filter((init) => init.method === "POST")
    .map((init) => JSON.parse(init.body as string));
}

beforeEach(() => {
  mockGeolocation(43.47234, -80.54489);
  accessTokenStore.set("abc");
});

afterEach(() => {
  vi.restoreAllMocks();
  toast.success.mockReset();
  toast.error.mockReset();
  accessTokenStore.clear();
});

describe("NewRequestForm", () => {
  it("submits the location rounded to the backend's precision", async () => {
    const user = userEvent.setup();
    const fetchSpy = mockFetchByPath({ "/requests/": jsonResponse(200, { data: CREATED }) });
    const { latitude, longitude } = await renderForm();
    expect(latitude).toHaveValue(43.47234);

    await user.click(screen.getByRole("button", { name: "Submit Request" }));

    await waitFor(() =>
      expect(toast.success).toHaveBeenCalledWith("Request submitted at (43.472, -80.545)"),
    );
    expect(postedBodies(fetchSpy)).toEqual([{ latitude: 43.472, longitude: -80.545 }]);
    // The form shows exactly what was sent.
    expect(latitude).toHaveValue(43.472);
    expect(longitude).toHaveValue(-80.545);
  });

  it("disables the submit button while the request is in flight", async () => {
    const user = userEvent.setup();
    let resolveRequest!: (response: Response) => void;
    const fetchSpy = mockFetchByPath({
      "/requests/": () =>
        new Promise<Response>((resolve) => {
          resolveRequest = resolve;
        }),
    });
    await renderForm();

    await user.click(screen.getByRole("button", { name: "Submit Request" }));
    const pending = await screen.findByRole("button", { name: "Submitting…" });
    expect(pending).toBeDisabled();
    await user.click(pending);
    expect(postedBodies(fetchSpy)).toHaveLength(1);

    resolveRequest(jsonResponse(200, { data: CREATED }));
    expect(await screen.findByRole("button", { name: "Submit Request" })).toBeEnabled();
  });

  it("shows the backend's error message when the request fails", async () => {
    const user = userEvent.setup();
    mockFetchByPath({
      "/requests/": jsonResponse(422, {
        detail: [{ loc: ["body", "latitude"], msg: "Input should be less than or equal to 90" }],
      }),
    });
    await renderForm();

    await user.click(screen.getByRole("button", { name: "Submit Request" }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Input should be less than or equal to 90"),
    );
    expect(toast.success).not.toHaveBeenCalled();
  });

  it("asks the user to log in when the session has expired", async () => {
    const user = userEvent.setup();
    mockFetchByPath({
      "/auth/rotate_tokens": jsonResponse(401),
      "/requests/": jsonResponse(401),
    });
    await renderForm();

    await user.click(screen.getByRole("button", { name: "Submit Request" }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Please log in to submit a request."),
    );
  });

  it("validates without calling the backend", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    await renderForm();

    await user.click(screen.getByRole("button", { name: "Validate Coordinates" }));

    expect(toast.success).toHaveBeenCalledWith("Coordinates validated and saved!");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("shows how to pick a location without a blocking alert", async () => {
    const alertSpy = vi.spyOn(window, "alert");
    await renderForm();

    expect(screen.getByText(/hold Shift and click a location on the map/)).toBeInTheDocument();
    expect(alertSpy).not.toHaveBeenCalled();
  });

  it("shows the rounded value even when it matches the saved coordinates", async () => {
    const user = userEvent.setup();
    const { latitude } = await renderForm();
    const validate = screen.getByRole("button", { name: "Validate Coordinates" });

    // Saves the rounded location, 43.472.
    await user.click(validate);
    expect(latitude).toHaveValue(43.472);

    // Rounds to the same 43.472, so the saved coordinates don't change.
    await user.clear(latitude);
    await user.type(latitude, "43.4724");
    await user.click(validate);

    expect(latitude).toHaveValue(43.472);
  });

  it("blocks out-of-range coordinates before sending anything", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const { latitude } = await renderForm();

    await user.clear(latitude);
    await user.type(latitude, "95");
    await user.click(screen.getByRole("button", { name: "Submit Request" }));

    expect(toast.error).toHaveBeenCalledWith("Please enter valid coordinates!");
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
