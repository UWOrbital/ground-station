import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL, jsonHeaders, parseOrThrow } from "@/lib/apiClient";
import type { Session } from "@/utils/types";

interface SessionsResponse {
  data: Session[];
}

/**
 * @brief Fetch comms sessions whose start time falls within a range.
 * @param startAfter only include sessions starting at or after this time.
 * @param startBefore only include sessions starting at or before this time.
 * @param limit maximum number of sessions to return.
 * @return list of sessions in the range.
 */
async function fetchSessionsInRange(
  startAfter: Date,
  startBefore: Date,
  limit: number,
): Promise<Session[]> {
  const params = new URLSearchParams({
    start_after: startAfter.toISOString(),
    start_before: startBefore.toISOString(),
    limit: String(limit),
  });
  const res = await fetch(`${API_BASE_URL}/sessions/?${params}`, {
    credentials: "include",
    headers: jsonHeaders(),
  });
  const json = await parseOrThrow<SessionsResponse>(res);
  return json.data;
}

const SESSIONS_POLL_INTERVAL_MS = 10_000;

/**
 * @brief React Query hook fetching comms sessions within a start-time range.
 * @param startAfter only include sessions starting at or after this time.
 * @param startBefore only include sessions starting at or before this time.
 * @param limit maximum number of sessions to return (defaults to 100).
 * @return useQuery result object with the list of sessions.
 */
export const useSessionsInRange = (startAfter: Date, startBefore: Date, limit: number = 100) => {
  return useQuery({
    queryKey: ["sessions", startAfter.toISOString(), startBefore.toISOString(), limit],
    queryFn: () => fetchSessionsInRange(startAfter, startBefore, limit),
    refetchInterval: SESSIONS_POLL_INTERVAL_MS,
  });
};
