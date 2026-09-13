import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_BASE_URL, jsonHeaders, parseOrThrow } from "@/lib/apiClient";
import type { Command } from "@/utils/types";

interface CommandResponse {
  data: Command;
}

interface CommandsResponse {
  data: Command[];
}

interface DeleteCommandResponse {
  message: string;
}

interface CreateCommandPayload {
  type_: number;
  params?: string;
  session_id: string;
  sequence_index?: number;
}

type UpdateCommandPayload = Partial<{ status: string; type_: number; params: string }>;

/**
 * @brief Fetch every command belonging to a comms session.
 * @param sessionId id of the session whose commands to fetch.
 * @return list of commands for the session.
 */
async function fetchCommandsBySession(sessionId: string): Promise<Command[]> {
  const res = await fetch(`${API_BASE_URL}/commands/session/${sessionId}`, {
    credentials: "include",
    headers: jsonHeaders(),
  });
  const json = await parseOrThrow<CommandsResponse>(res);
  return json.data;
}

/**
 * @brief Create a new command.
 * @param payload command fields to create.
 * @return the created command.
 */
async function createCommand(payload: CreateCommandPayload): Promise<Command> {
  const res = await fetch(`${API_BASE_URL}/commands/`, {
    method: "POST",
    credentials: "include",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  const json = await parseOrThrow<CommandResponse>(res);
  return json.data;
}

/**
 * @brief Update an existing command.
 * @param commandId id of the command to update.
 * @param payload partial command fields to change.
 * @return the updated command.
 */
async function updateCommand(commandId: string, payload: UpdateCommandPayload): Promise<Command> {
  const res = await fetch(`${API_BASE_URL}/commands/${commandId}`, {
    method: "PATCH",
    credentials: "include",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  const json = await parseOrThrow<CommandResponse>(res);
  return json.data;
}

/**
 * @brief Delete a command.
 * @param commandId id of the command to delete.
 * @return the delete confirmation message.
 */
async function deleteCommand(commandId: string): Promise<DeleteCommandResponse> {
  const res = await fetch(`${API_BASE_URL}/commands/${commandId}`, {
    method: "DELETE",
    credentials: "include",
    headers: jsonHeaders(),
  });
  return parseOrThrow<DeleteCommandResponse>(res);
}

const COMMANDS_POLL_INTERVAL_MS = 2_000;

/**
 * @brief React Query hook fetching the commands for a session.
 *
 * Disabled until a session id is provided, and polls while enabled so the
 * table reflects command status changes during a pass.
 *
 * @param sessionId id of the session whose commands to fetch, or null.
 * @return useQuery result object with the list of commands.
 */
export const useCommandsBySession = (sessionId: string | null) => {
  return useQuery({
    queryKey: ["commands", sessionId],
    queryFn: () => fetchCommandsBySession(sessionId as string),
    enabled: !!sessionId,
    refetchInterval: COMMANDS_POLL_INTERVAL_MS,
  });
};

/**
 * @brief React Query mutation hook that creates a command.
 *
 * On success it invalidates the affected session's command list so the
 * table refreshes.
 *
 * @return useMutation result object; call mutate/mutateAsync with the payload.
 */
export const useCreateCommand = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateCommandPayload) => createCommand(payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["commands", variables.session_id] });
    },
  });
};

/**
 * @brief React Query mutation hook that updates a command.
 *
 * On success it invalidates all command lists so tables refresh.
 *
 * @return useMutation result object; call mutate/mutateAsync with the id and payload.
 */
export const useUpdateCommand = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ commandId, payload }: { commandId: string; payload: UpdateCommandPayload }) =>
      updateCommand(commandId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commands"] });
    },
  });
};

/**
 * @brief React Query mutation hook that deletes a command.
 *
 * On success it invalidates all command lists so tables refresh.
 *
 * @return useMutation result object; call mutate/mutateAsync with the command id.
 */
export const useDeleteCommand = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (commandId: string) => deleteCommand(commandId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commands"] });
    },
  });
};
