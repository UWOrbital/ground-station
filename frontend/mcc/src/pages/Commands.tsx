import { createColumnHelper } from "@tanstack/react-table";
import Table from "../components/Table";
import type { Command, MainCommand, Session } from "../utils/types";
import SelectCommand from "./SelectCommand";
// import SendCommand from "./components/SendCommand";
import { useState, useEffect, useCallback, useMemo } from "react";
import { getSessionsInRange } from "../utils/api/sessions";
import { getMainCommands } from "../utils/api/mainCommands";
import { getCommandsBySession } from "@/utils/api/commands";

type CommandRow = {
  id: string;
  command: string;
  status: Command["status"];
  params: string;
  created_at: string;
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
];

/**
 * @brief Commands component displaying the commands table
 * @return tsx element of Commands component
 */
function Commands() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [mainCommands, setMainCommands] = useState<MainCommand[]>([]);
  const [commands, setCommands] = useState<Command[]>([]);
  const [selectedCommandId, setSelectedCommandId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const now = new Date();
    const in72Hours = new Date(now.getTime() + 72 * 60 * 60 * 1000);
    getSessionsInRange(now, in72Hours)
      .then((data) => {
        setSessions(data);
        if (data.length > 0) setSelectedSessionId(data[0].id);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load sessions"));

    getMainCommands()
      .then(setMainCommands)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load command catalog"));
  }, []);

  const refetchCommands = useCallback(() => {
    if (!selectedSessionId) return;
    setLoading(true);
    getCommandsBySession(selectedSessionId)
      .then(setCommands)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load commands"))
      .finally(() => setLoading(false));
  }, [selectedSessionId]);

  useEffect(() => {
    refetchCommands();
  }, [refetchCommands]);

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
  }));

  // const selectedSession = sessions.find((s) => s.id === selectedCommandId) ?? null;
  // const selectedMainCommand = mainCommands.find((mc) => mc.id === selectedCommandId) ?? null;

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

      <div className="min-h-screen w-full flex justify-center items-center space-x-10">
        {loading ? (
          <p className="text-gray-400">Loading commands...</p>
        ) : (
          <Table data={rows} columns={columns} showFilters={true} />
        )}
      </div>
      <SelectCommand mainCommands={mainCommands} selectedCommandId={selectedCommandId} setSelectedCommandId={setSelectedCommandId} />
    </div>
  );
}

export default Commands;
