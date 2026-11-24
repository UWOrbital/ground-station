import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { createQueryWrapper, jsonResponse } from "@/hooks/testUtils";
import type { PictureRequest } from "@/hooks/usePictureRequests";
import { accessTokenStore } from "@/lib/authToken";
import toastService from "@/services/Toast.service";
import Requests from "./requests";

const DELETE_URL = "http://localhost:8000/api/aro/requests/aaaa";

/**
 * @brief Build a picture request list item with sensible defaults.
 * @param overrides fields to replace on the default request.
 * @return a PictureRequest as the list endpoint returns it.
 */
function makeRequest(overrides: Partial<PictureRequest> = {}): PictureRequest {
  return {
    id: "aaaa",
    aro_id: "user",
    latitude: 43.47,
    longitude: -80.54,
    created_on: "2026-01-01T00:00:00Z",
    request_sent_to_obc_on: null,
    pic_taken_on: null,
    pic_transmitted_on: null,
    delete_deadline: "2026-01-01T00:10:00Z",
    packet_id: null,
    status: "pending",
    operations: {},
    ...overrides,
  };
}

/**
 * @brief Build a successful list endpoint response.
 * @param requests the requests to return.
 * @return the fake list Response.
 */
function listResponse(requests: PictureRequest[]): Response {
  return jsonResponse(200, { data: requests, operations: {} });
}

/**
 * @brief Render the Requests page inside the router and query providers.
 */
function renderPage(): void {
  render(
    <MemoryRouter>
      <Requests />
    </MemoryRouter>,
    { wrapper: createQueryWrapper() },
  );
}

beforeEach(() => {
  accessTokenStore.set("abc");
});

afterEach(() => {
  vi.restoreAllMocks();
  accessTokenStore.clear();
});

describe("Requests", () => {
  it("shows Delete only for requests the backend marks deletable", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      listResponse([
        makeRequest({
          id: "aaaa",
          operations: {
            delete: { url: DELETE_URL, deletable_until: "2026-01-01T00:10:00Z" },
          },
        }),
        // Pending and inside its deadline, but no delete operation: must not be deletable.
        makeRequest({ id: "bbbb", latitude: 10, operations: {} }),
      ]),
    );
    renderPage();

    const rows = await screen.findAllByRole("row");
    // header row + two requests
    expect(rows).toHaveLength(3);
    expect(within(rows[1]).getByRole("button", { name: "Delete" })).toBeInTheDocument();
    expect(within(rows[2]).queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });

  it("deletes through the advertised URL after confirming and refetches the list", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const success = vi.spyOn(toastService, "success").mockImplementation(() => {});
    const deletable = makeRequest({
      operations: { delete: { url: DELETE_URL, deletable_until: "2026-01-01T00:10:00Z" } },
    });
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(listResponse([deletable]))
      .mockResolvedValueOnce(jsonResponse(200, { data: deletable }))
      .mockResolvedValueOnce(listResponse([]));
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Delete" }));

    expect(await screen.findByText("You haven't made any requests yet.")).toBeInTheDocument();
    expect(String(fetchSpy.mock.calls[1][0])).toBe(DELETE_URL);
    expect((fetchSpy.mock.calls[1][1] as RequestInit).method).toBe("DELETE");
    expect(String(fetchSpy.mock.calls[2][0])).toContain("/requests/?");
    expect(success).toHaveBeenCalledWith("Picture request deleted.");
  });

  it("does not delete when the user cancels the confirmation", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      listResponse([
        makeRequest({
          operations: { delete: { url: DELETE_URL, deletable_until: "2026-01-01T00:10:00Z" } },
        }),
      ]),
    );
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Delete" }));

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("shows the backend error and refreshes when the delete is refused", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const error = vi.spyOn(toastService, "error").mockImplementation(() => {});
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        listResponse([
          makeRequest({
            operations: { delete: { url: DELETE_URL, deletable_until: "2026-01-01T00:10:00Z" } },
          }),
        ]),
      )
      .mockResolvedValueOnce(
        jsonResponse(409, { message: "This picture request can no longer be deleted." }),
      )
      // The window closed, so the backend no longer advertises delete.
      .mockResolvedValueOnce(listResponse([makeRequest({ operations: {} })]));
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Delete" }));

    await vi.waitFor(() =>
      expect(error).toHaveBeenCalledWith("This picture request can no longer be deleted."),
    );
    await vi.waitFor(() =>
      expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument(),
    );
    expect(fetchSpy).toHaveBeenCalledTimes(3);
  });

  it("shows an empty state when the user has no requests", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(listResponse([]));
    renderPage();

    expect(await screen.findByText("You haven't made any requests yet.")).toBeInTheDocument();
  });

  it("shows an error when the list fails to load", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(500, { detail: "boom" }));
    renderPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to load your requests.");
  });
});
