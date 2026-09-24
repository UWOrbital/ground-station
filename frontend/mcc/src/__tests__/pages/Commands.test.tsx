import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Commands from "@/pages/Commands";
import { useSessionsInRange } from "@/hooks/useSessions";
import { useMainCommands } from "@/hooks/useMainCommands";
import { useCommandsBySession, useCreateCommand } from "@/hooks/useCommands";
import type { Command, MainCommand, Session } from "@/utils/types";

vi.mock("@/hooks/useSessions", () => ({ useSessionsInRange: vi.fn() }));
vi.mock("@/hooks/useMainCommands", () => ({ useMainCommands: vi.fn() }));
vi.mock("@/hooks/useCommands", () => ({
  useCommandsBySession: vi.fn(),
  useCreateCommand: vi.fn(),
}));

const sessions: Session[] = [
  { id: "ses-1", start_time: "2099-01-01T00:00:00Z", end_time: null, status: "scheduled" },
  { id: "ses-2", start_time: "2099-01-02T00:00:00Z", end_time: null, status: "pending" },
];

const mainCommands: MainCommand[] = [
  { id: 1, name: "PING", params: null, format: null, data_size: 0, total_size: 8, priority: 0 },
  {
    id: 2,
    name: "SET_RATE",
    params: "rate",
    format: "int",
    data_size: 4,
    total_size: 12,
    priority: 1,
  },
];

const commands: Command[] = [
  {
    id: "c1",
    user_id: null,
    session_id: "ses-1",
    status: "failed",
    type_: 2,
    params: "5",
    created_at: "2099-01-01T00:00:00Z",
    packet_id: null,
    sequence_index: 3,
    response: "NACK",
  },
  {
    id: "c2",
    user_id: null,
    session_id: "ses-1",
    status: "completed",
    type_: 99,
    params: null,
    created_at: "2099-01-01T00:00:00Z",
    packet_id: null,
    sequence_index: null,
    response: null,
  },
];

type Query = { data?: unknown; error?: Error | null; isLoading?: boolean };

const setup = ({
  sessionsQuery = { data: sessions },
  commandsQuery = { data: commands },
}: { sessionsQuery?: Query; commandsQuery?: Query } = {}) => {
  const mutateAsync = vi.fn().mockResolvedValue({});
  vi.mocked(useSessionsInRange).mockReturnValue(
    sessionsQuery as ReturnType<typeof useSessionsInRange>,
  );
  vi.mocked(useMainCommands).mockReturnValue({ data: mainCommands } as ReturnType<
    typeof useMainCommands
  >);
  vi.mocked(useCommandsBySession).mockReturnValue(
    commandsQuery as ReturnType<typeof useCommandsBySession>,
  );
  vi.mocked(useCreateCommand).mockReturnValue({ mutateAsync } as unknown as ReturnType<
    typeof useCreateCommand
  >);

  const queryClient = new QueryClient();
  const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
  render(
    <QueryClientProvider client={queryClient}>
      <Commands />
    </QueryClientProvider>,
  );
  return { mutateAsync, invalidateQueries };
};

describe("Commands Page", () => {
  it("auto-selects the first session and loads its commands", () => {
    setup();
    expect(screen.getByRole("combobox")).toHaveValue("ses-1");
    expect(useCommandsBySession).toHaveBeenLastCalledWith("ses-1");
  });

  it("renders command rows using main command names", () => {
    setup();
    const [, failedRow, unknownRow] = screen.getAllByRole("row");

    expect(within(failedRow).getByText("SET_RATE")).toBeInTheDocument();
    expect(within(failedRow).getByText("failed")).toHaveClass("text-red-400");
    expect(within(failedRow).getByText("NACK")).toBeInTheDocument();
    expect(within(failedRow).getByText("3")).toBeInTheDocument();

    expect(within(unknownRow).getByText("Unknown (#99)")).toBeInTheDocument();
    expect(within(unknownRow).getByText("0")).toBeInTheDocument();
  });

  it("loads commands for a session picked from the dropdown", async () => {
    setup();
    await userEvent.selectOptions(screen.getByRole("combobox"), "ses-2");
    expect(useCommandsBySession).toHaveBeenLastCalledWith("ses-2");
  });

  it("shows a query error", () => {
    setup({ sessionsQuery: { data: sessions, error: new Error("Sessions unavailable") } });
    expect(screen.getByText("Sessions unavailable")).toBeInTheDocument();
  });

  it("shows a loading overlay while the selected session's commands load", () => {
    setup({ commandsQuery: { isLoading: true } });
    expect(screen.getByText("Loading commands...")).toBeInTheDocument();
  });

  it("selects nothing and shows no overlay when there are no sessions", () => {
    setup({ sessionsQuery: { data: [] }, commandsQuery: { isLoading: true } });
    expect(useCommandsBySession).toHaveBeenLastCalledWith(null);
    expect(screen.queryByText("Loading commands...")).not.toBeInTheDocument();
  });

  it("sends a command picked from the menu and refreshes that session's commands", async () => {
    const { mutateAsync, invalidateQueries } = setup();
    expect(screen.queryByRole("button", { name: "Submit" })).not.toBeInTheDocument();

    await userEvent.click(document.querySelector("[aria-haspopup='menu']")!);
    await userEvent.click(screen.getByRole("menuitemcheckbox", { name: "PING" }));
    await userEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ type_: 1, session_id: "ses-1" }),
    );
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["commands", "ses-1"] });
  });
});
