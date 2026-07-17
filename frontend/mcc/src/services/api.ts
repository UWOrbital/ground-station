/**
 * Base API configuration for the MCC backend.
 */

const API_BASE_URL: string =
  import.meta.env.VITE_MCC_API_BASE_URL ?? "http://localhost:8000/api/v1/mcc";

/**
 * @brief Sends a POST request to the MCC backend.
 * @param endpoint - The API endpoint path (e.g. "/passes/{session_id}/prepare-keys").
 * @param body - Optional request body to send as JSON.
 * @return The parsed JSON response.
 * @throws Error if the response status is not OK.
 */
export async function apiPost<TResponse>(endpoint: string, body?: unknown): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => "Unknown error");
    throw new Error(`POST ${endpoint} failed (${response.status}): ${errorBody}`);
  }

  return response.json() as Promise<TResponse>;
}

/**
 * @brief Sends a GET request to the MCC backend.
 * @param endpoint - The API endpoint path.
 * @return The parsed JSON response.
 * @throws Error if the response status is not OK.
 */
export async function apiGet<TResponse>(endpoint: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => "Unknown error");
    throw new Error(`GET ${endpoint} failed (${response.status}): ${errorBody}`);
  }

  return response.json() as Promise<TResponse>;
}

export default {
  apiPost,
  apiGet,
};
