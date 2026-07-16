import { API_BASE_URL } from "./config";
import { jsonHeaders, parseOrThrow } from "./auth";
import type { MainCommand } from "../types";

interface MainCommandsResponse {
  data: MainCommand[];
}

export async function getMainCommands(): Promise<MainCommand[]> {
  const res = await fetch(`${API_BASE_URL}/main-commands/`, {
    credentials: "include",
    headers: jsonHeaders(),
  });
  const json = await parseOrThrow<MainCommandsResponse>(res);
  return json.data;
}
