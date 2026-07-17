import { apiPost } from "./api";

export interface PrepareKeysResponse {
  message: string;
  count: number;
}

/**
 * @brief Prepares all unsynced active ARO keys for the given comms session.
 * @param sessionId - The UUID of the comms session.
 * @return Object containing a message and the count of prepared commands.
 */
export async function prepareKeysForSession(sessionId: string): Promise<PrepareKeysResponse> {
  return apiPost<PrepareKeysResponse>(`/passes/${sessionId}/prepare-keys`);
}
