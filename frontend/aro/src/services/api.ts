/**
 * @brief Base API configuration for ARO frontend
 */

const ARO_API_BASE_URL = import.meta.env.VITE_ARO_API_BASE_URL ?? "http://localhost:8000/api/v1/aro";

/**
 * @brief Get the auth token from localStorage
 * @return the stored X-Auth-Token value, or null if not present
 */
export function getAuthToken(): string | null {
  return localStorage.getItem("aro_auth_token");
}

/**
 * @brief Build headers with auth token for API requests
 * @param additionalHeaders optional additional headers to include
 * @return Headers object with Content-Type and X-Auth-Token set
 */
export function buildAuthHeaders(additionalHeaders?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...additionalHeaders,
  };

  const token = getAuthToken();
  if (token) {
    headers["X-Auth-Token"] = token;
  }

  return headers;
}

/**
 * @brief Perform an authenticated GET request to the ARO API
 * @param path the API path relative to the base URL
 * @return parsed JSON response
 * @throws Error if the response is not ok
 */
export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${ARO_API_BASE_URL}${path}`, {
    method: "GET",
    headers: buildAuthHeaders(),
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => "Unknown error");
    throw new Error(`GET ${path} failed (${response.status}): ${errorBody}`);
  }

  return response.json() as Promise<T>;
}

/**
 * @brief Perform an authenticated POST request to the ARO API
 * @param path the API path relative to the base URL
 * @param body the JSON request body
 * @return parsed JSON response
 * @throws Error if the response is not ok
 */
export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${ARO_API_BASE_URL}${path}`, {
    method: "POST",
    headers: buildAuthHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => "Unknown error");
    throw new Error(`POST ${path} failed (${response.status}): ${errorBody}`);
  }

  return response.json() as Promise<T>;
}
