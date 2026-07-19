import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Telemetry from "./Telemetry";

const mockTelemetryData = {
  data: [
    {
      id: "a1b2c3d4-0000-0000-0000-000000000001",
      type: "Battery Voltage",
      value: "3.7",
      timestamp: "2025-06-01T12:00:05Z",
      subrows: [
        {
          packet: "pkt-1111-1111",
          session: "ses-1111-1111",
          obc_state: "completed",
        },
      ],
    },
    {
      id: "a1b2c3d4-0000-0000-0000-000000000002",
      type: "Temperature",
      value: "25.0",
      timestamp: "2025-06-01T12:00:10Z",
      subrows: null,
    },
  ],
};

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

function renderTelemetry() {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Telemetry />
      </BrowserRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Telemetry Page", () => {
  it("shows a loading message while data is being fetched", async () => {
    // Never resolve the fetch so the query stays in loading state
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => {}));

    renderTelemetry();

    expect(screen.getByText(/loading telemetry data/i)).toBeInTheDocument();
  });

  it("shows an error message when the fetch fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    renderTelemetry();

    await waitFor(() => {
      expect(screen.getByText(/failed to load telemetry/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/network error/i)).toBeInTheDocument();
  });

  it("renders telemetry rows from the API response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockTelemetryData,
    } as Response);

    renderTelemetry();

    // Wait for the table values to appear (unique to cells, not in dropdown options)
    await waitFor(() => {
      expect(screen.getByText("3.7")).toBeInTheDocument();
    });

    expect(screen.getByText("25.0")).toBeInTheDocument();
    // Type names appear in both table cells and the dropdown — verify at least one
    expect(screen.getAllByText("Battery Voltage").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Temperature").length).toBeGreaterThanOrEqual(1);
  });

  it("shows an empty-state message when the API returns no data", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ data: [] }),
    } as Response);

    renderTelemetry();

    await waitFor(() => {
      expect(screen.getByText(/no telemetry data matches/i)).toBeInTheDocument();
    });
  });

  it("filters table rows via the search input", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockTelemetryData,
    } as Response);

    renderTelemetry();

    // Wait for data to render
    await waitFor(() => {
      expect(screen.getByText("3.7")).toBeInTheDocument();
    });

    const user = userEvent.setup();
    const searchInput = screen.getByPlaceholderText("Search...");
    await user.type(searchInput, "Temperature");

    // Battery Voltage's value should no longer be visible (row filtered out)
    expect(screen.queryByText("3.7")).not.toBeInTheDocument();
    // Temperature's value should remain visible
    expect(screen.getByText("25.0")).toBeInTheDocument();
  });

  it("filters table rows via the type dropdown", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockTelemetryData,
    } as Response);

    renderTelemetry();

    await waitFor(() => {
      expect(screen.getByText("3.7")).toBeInTheDocument();
    });

    const user = userEvent.setup();
    const typeSelect = screen.getByRole("combobox");
    await user.selectOptions(typeSelect, "Temperature");

    // Battery Voltage's value should be filtered out of the table
    expect(screen.queryByText("3.7")).not.toBeInTheDocument();
    expect(screen.getByText("25.0")).toBeInTheDocument();
  });

  it("shows column headers", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockTelemetryData,
    } as Response);

    renderTelemetry();

    await waitFor(() => {
      expect(screen.getByText("Value")).toBeInTheDocument();
    });

    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getByText("Timestamp")).toBeInTheDocument();
  });
});
