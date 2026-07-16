import { API_BASE_URL } from "./config";
import { jsonHeaders, parseOrThrow } from "./auth";
import type { Session } from "../types";

interface SessionsResponse {
  data: Session[];
}

export async function getSessionsInRange(startAfter: Date, startBefore: Date, limit: number = 100): Promise<Session[]> {
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
