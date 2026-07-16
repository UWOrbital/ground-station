import { API_BASE_URL } from "./config";
import { jsonHeaders, parseOrThrow } from "./auth";
import type { Command } from "../types";

interface CommandResponse {
  data: Command;
}

interface CommandsResponse {
  data: Command[];
}

interface DeleteCommandResponse {
  message: string;
}

export async function getCommandsBySession(sessionId: string): Promise<Command[]> {
  const res = await fetch(`${API_BASE_URL}/commands/session/${sessionId}`, {
    credentials: "include",
    headers: jsonHeaders(),
  });
  const json = await parseOrThrow<CommandsResponse>(res);
  return json.data;
}

export async function createCommand(payload: {
  type_: number;
  params?: string;
  session_id: string;
}): Promise<Command> {
  const res = await fetch(`${API_BASE_URL}/commands/`, {
    method: "POST",
    credentials: "include",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  const json = await parseOrThrow<CommandResponse>(res);
  return json.data;
}

export async function updateCommand(
  commandId: string,
  payload: Partial<{ status: string; type_: number; params: string }>,
): Promise<Command> {
  const res = await fetch(`${API_BASE_URL}/commands/${commandId}`, {
    method: "PATCH",
    credentials: "include",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  const json = await parseOrThrow<CommandResponse>(res);
  return json.data;
}

export async function deleteCommand(commandId: string): Promise<DeleteCommandResponse> {
  const res = await fetch(`${API_BASE_URL}/commands/${commandId}`, {
    method: "DELETE",
    credentials: "include",
    headers: jsonHeaders(),
  });
  return parseOrThrow<DeleteCommandResponse>(res);
}
