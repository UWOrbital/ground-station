import { createColumnHelper } from "@tanstack/react-table";
import { useRef, useEffect, useState } from "react";
import Table from "../components/Table";
import type { Session, SessionStatus } from "../utils/types";
import { useSessionsInRange } from "../hooks/useSessions";

const statusColors: Record<SessionStatus, string> = {
  pending: "text-yellow-400",
  scheduled: "text-blue-400",
  ongoing: "text-green-400",
  completed: "text-teal-400",
};

const columnHelper = createColumnHelper<Session>();

const columns = [
  columnHelper.accessor("start_time", {
    header: "Start",
    cell: (info) => new Date(info.getValue()).toLocaleString(),
  }),
  columnHelper.accessor("end_time", {
    header: "End",
    cell: (info) => {
      const v = info.getValue();
      return v ? new Date(v).toLocaleString() : "--";
    },
  }),
  columnHelper.accessor("status", {
    header: "Status",
    cell: (info) => <span className={statusColors[info.getValue()]}>{info.getValue()}</span>,
  }),
  columnHelper.accessor("id", {
    header: "Session ID",
    cell: (info) => info.getValue(),
  }),
];

function LiveCard({ session }: { session: Session | null }) {
  if (!session)
    return (
      <div className="w-full max-w-5xl border border-border bg-card rounded-lg p-6 text-center">
        <p className="text-yellow-400">No live session right now.</p>
        <p className="text-sm text-muted-foreground">
          Shows here when a session is ongoing; scheduled ones appear in the table below.
        </p>
      </div>
    );

  const duration = Math.max(
    0,
    Math.floor(
      ((session.end_time ? new Date(session.end_time) : new Date()).getTime() -
        new Date(session.start_time).getTime()) /
        60000,
    ),
  );

  return (
    <div className="w-full max-w-5xl border border-border bg-card rounded-lg p-6">
      <div className="flex items-center gap-3 mb-4">
        <span className="relative flex h-3 w-3">
          <span className="absolute inline-flex h-full w-full rounded-full bg-green-500 animate-pulse" />
          <span className="absolute inline-flex h-full w-full rounded-full bg-green-400 animate-ping" />
        </span>
        <h2 className="text-lg font-semibold text-foreground">Live session</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">Started</p>
          <p className="text-sm text-foreground">{new Date(session.start_time).toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">Duration</p>
          <p className="text-sm text-foreground">{duration} min</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">Session ID</p>
          <p className="text-sm text-foreground break-all">{session.id}</p>
        </div>
      </div>
    </div>
  );
}

function LiveSession() {
  const now = useRef(new Date()); // pinned per mount; a fresh query key each render would refetch endlessly
  const past7Days = new Date(now.current.getTime() - 7 * 24 * 60 * 60 * 1000);
  const in24Hours = new Date(now.current.getTime() + 24 * 60 * 60 * 1000);

  const {
    data: sessions,
    isLoading,
    isError,
    error,
  } = useSessionsInRange(past7Days, in24Hours, 500);

  const [, setTick] = useState(0); // ticks each minute so the live duration counts up between polls
  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 60_000);
    return () => clearInterval(t);
  }, []);

  const live = sessions?.find((s) => s.status === "ongoing") ?? null;
  const rows = [...(sessions ?? [])].reverse(); // backend returns oldest first

  if (isLoading)
    return (
      <div className="flex items-center justify-center min-h-[80vh]">
        <p className="text-muted-foreground text-lg">Loading sessions…</p>
      </div>
    );

  if (isError)
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] gap-2">
        <p className="text-red-400 text-lg">Failed to load sessions.</p>
        <p className="text-muted-foreground text-sm">{(error as Error)?.message}</p>
      </div>
    );

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 pt-8 gap-10">
      <LiveCard session={live} />
      <Table
        data={rows}
        columns={columns}
        showFilters={true}
        containerClassName="w-full max-w-5xl"
      />
      {rows.length === 0 && (
        <p className="text-muted-foreground">No sessions in the last 7 days.</p>
      )}
    </div>
  );
}

export default LiveSession;
