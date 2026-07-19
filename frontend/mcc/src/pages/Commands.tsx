import { createColumnHelper } from "@tanstack/react-table";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Table from "../components/Table";
import type { Command } from "../utils/types";
import SelectCommand from "./SelectCommand";
import SendCommand from "./SendCommand";
import { useState, useEffect, useMemo } from "react";
import { getSessionsInRange } from "../utils/api/sessions";
import { getMainCommands } from "../utils/api/mainCommands";
import { getCommandsBySession } from "@/utils/api/commands";

type CommandRow = {
  id: string;
  command: string;
  status: Command["status"];
  params: string;
  created_at: string;
  sequence_index: number;
  response: string;
};

const statusColors: Record<string, string> = {
  pending: "text-yellow-400",
  scheduled: "text-blue-400",
  ongoing: "text-green-400",
  cancelled: "text-gray-400",
  failed: "text-red-400",
  completed: "text-teal-400",
};

const columnHelper = createColumnHelper<CommandRow>();

const columns = [
  columnHelper.accessor("command", {
    header: "Command",
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor("status", {
    header: "Status",
    cell: (info) => {
      const status = info.getValue();
      return <span className={statusColors[status] || "text-gray-400"}>{status}</span>;
    },
  }),
  columnHelper.accessor("params", {
    header: "Parameters",
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor("created_at", {
    header: "Created",
    cell: (info) => new Date(info.getValue()).toLocaleString(),
  }),
  columnHelper.accessor("sequence_index", {
    header: "Sequence index",
    cell: (info) => info.getValue().toLocaleString(),
  }),
  columnHelper.accessor("response", {
    header: "Response",
    cell: (info) => info.getValue(),
  }),
];

const SESSIONS_POLL_INTERVAL_MS = 10_000;
const COMMANDS_POLL_INTERVAL_MS = 2_000;

/**
 * @brief Commands component displaying the commands table
 * @return tsx element of Commands component
 */
function Commands() {
  const queryClient = useQueryClient();
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedCommandId, setSelectedCommandId] = useState<number | null>(null);

  const sessionsQuery = useQuery({
    queryKey: ["sessions", "upcoming-and-recent"],
    queryFn: () => {
      const now = new Date();
      const past30Min = new Date(now.getTime() - 30 * 60 * 1000);
      const in72Hours = new Date(now.getTime() + 72 * 60 * 60 * 1000);
      return getSessionsInRange(past30Min, in72Hours, 100);
    },
    refetchInterval: SESSIONS_POLL_INTERVAL_MS,
  });

  const mainCommandsQuery = useQuery({
    queryKey: ["mainCommands"],
    queryFn: getMainCommands,
  });

  const commandsQuery = useQuery({
    queryKey: ["commands", selectedSessionId],
    queryFn: () => getCommandsBySession(selectedSessionId as string),
    enabled: !!selectedSessionId,
    refetchInterval: COMMANDS_POLL_INTERVAL_MS,
  });

  const sessions = useMemo(() => sessionsQuery.data ?? [], [sessionsQuery.data])
  const mainCommands = useMemo(() => mainCommandsQuery.data ?? [], [mainCommandsQuery.data])
  const commands = useMemo(() => commandsQuery.data ?? [], [commandsQuery.data])

  useEffect(() => {
    if (!selectedSessionId && sessions.length > 0) {
      setSelectedSessionId(sessions[0].id);
    }
  }, [sessions, selectedSessionId]);

  const error = (sessionsQuery.error as Error | undefined)?.message ??
  (mainCommandsQuery.error as Error | undefined)?.message ??
  (commandsQuery.error as Error | undefined)?.message ?? null;

  const mainCommandsById = useMemo(
    () => new Map(mainCommands.map((mc) => [mc.id, mc])),
    [mainCommands],
  );

  const rows: CommandRow[] = commands.map((cmd) => ({
    id: cmd.id,
    command: mainCommandsById.get(cmd.type_)?.name ?? `Unknown (#${cmd.type_})`,
    status: cmd.status,
    params: cmd.params ?? "",
    created_at: cmd.created_at,
    sequence_index: cmd.sequence_index ?? 0,
    response: cmd.response ?? "",
  }));

  const selectedSession = sessions.find((s) => s.id === selectedSessionId) ?? null;
  const selectedMainCommand = mainCommands.find((mc) => mc.id === selectedCommandId) ?? null;

  const handleSubmitted = () => {
    queryClient.invalidateQueries( { queryKey: ["commands", selectedSessionId ]});
  };

  return (
    <div>
      <div className="flex justify-center pt-6">
        <select
          className="bg-gray-800 text-white px-3 py-2 rounded-md border border-gray-600"
          value={selectedSessionId ?? ""}
          onChange={(e) => setSelectedSessionId(e.target.value || null)}
        >
          <option value="" disabled>
            Select a session
          </option>
          {sessions.map((s) => (
            <option key={s.id} value={s.id}>
              {new Date(s.start_time).toLocaleString()} ({s.status})
            </option>
          ))}
        </select>
      </div>

      {error && <p className="text-red-400 text-center mt-4">{error}</p>}

      <div className="w-full flex justify-center items-start gap-10 pt-6">
        {selectedCommandId && (
          <SendCommand
            mainCommand={selectedMainCommand}
            selectedSessionId={selectedSessionId}
            sessionStartTime={selectedSession?.start_time ?? null}
            setSelectedCommandId={setSelectedCommandId}
            onSubmitted={handleSubmitted}
          />
        )}
        <Table data={rows} columns={columns} showFilters={true} />
        {commandsQuery.isLoading && !!selectedSessionId && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-sm">
            <p className="text-gray-400">Loading commands...</p>
          </div>
        )}
      </div>
      <SelectCommand
        mainCommands={mainCommands}
        selectedCommandId={selectedCommandId}
        setSelectedCommandId={setSelectedCommandId}
      />
    </div>
  );
}

export default Commands;
