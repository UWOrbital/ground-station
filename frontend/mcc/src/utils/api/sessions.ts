import { API_BASE_URL } from "./config";
import { jsonHeaders, parseOrThrow } from "./auth";
import type { Session } from "../types";

interface SessionsResponse {
  data: Session[];
}

export async function getSessions(): Promise<Session[]> {
  const res = await fetch(`${API_BASE_URL}/sessions/`, {
    credentials: "include",
    headers: jsonHeaders(),
  });
  const json = await parseOrThrow<SessionsResponse>(res);
  return json.data;
}
