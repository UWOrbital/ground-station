import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LiveSession from "./LiveSession";

const mockSessions = {
  data: [
    {
      id: "a1b2c3d4-0000-0000-0000-000000000001",
      start_time: "2026-09-13T10:00:00Z",
      end_time: "2026-09-13T10:30:00Z",
      status: "completed",
    },
    {
      id: "a1b2c3d4-0000-0000-0000-000000000002",
      start_time: "2026-09-14T12:00:00Z",
      end_time: "2026-09-14T12:45:00Z",
      status: "ongoing",
    },
  ],
};

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
}

function renderLiveSession() {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <LiveSession />
      </BrowserRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("LiveSession Page", () => {
  it("shows a loading message while sessions are fetched", () => {
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => {}));

    renderLiveSession();

    expect(screen.getByText(/loading sessions/i)).toBeInTheDocument();
  });

  it("shows an error message when the fetch fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    renderLiveSession();

    await waitFor(() => {
      expect(screen.getByText(/failed to load sessions/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/network error/i)).toBeInTheDocument();
  });

  it("renders the live session card from the ongoing session", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockSessions,
    } as Response);

    renderLiveSession();

    await waitFor(() => {
      expect(screen.getByText("Live session")).toBeInTheDocument();
    });

    // The ongoing session's ID appears in both the live card and the table row
    expect(screen.getAllByText(mockSessions.data[1].id).length).toBe(2);
    expect(screen.getByText("45 min")).toBeInTheDocument();
  });

  it("shows the no-live-session card when no session is ongoing", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        data: [mockSessions.data[0]], // completed only
      }),
    } as Response);

    renderLiveSession();

    await waitFor(() => {
      expect(screen.getByText(/no live session right now/i)).toBeInTheDocument();
    });
  });

  it("renders all sessions newest-first in the table", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockSessions,
    } as Response);

    renderLiveSession();

    await waitFor(() => {
      expect(screen.getByText(mockSessions.data[0].id)).toBeInTheDocument();
    });

    const table = screen.getByRole("table");
    const firstId = table.querySelector("tbody tr td:last-child")?.textContent;
    expect(firstId).toBe(mockSessions.data[1].id); // ongoing session listed first
  });

  it("shows an empty-state message when there are no sessions", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ data: [] }),
    } as Response);

    renderLiveSession();

    await waitFor(() => {
      expect(screen.getByText(/no sessions in the last 7 days/i)).toBeInTheDocument();
    });
  });
});
