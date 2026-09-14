/**
 * Shared ARO API client infrastructure.
 *
 * Holds the base URL, the typed error class, and the low-level request
 * helpers shared by every API hook under `src/hooks`. These are pure
 * helpers (no React), so they live here rather than in a hook.
 *
 * Mirrors the MCC client (`frontend/mcc/src/lib/apiClient.ts`); the one
 * intentional difference is 401 handling: ARO authenticates via a
 * POST-only `/api/aro/auth/login` (JWT access token plus refresh cookie),
 * so there is no backend redirect endpoint to send the browser to. On 401
 * we redirect to the ARO frontend `/login` route instead.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/aro";

const LOGIN_ROUTE = "/login";

/**
 * Error thrown by {@link parseOrThrow} carrying the HTTP status code.
 */
export class ApiError extends Error {
  status: number;

  /**
   * @brief Construct an ApiError.
   * @param status HTTP status code of the failed response.
   * @param message human-readable error message.
   */
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/**
 * @brief Build the default JSON request headers.
 * @return headers object requesting/sending JSON.
 */
export function jsonHeaders(): HeadersInit {
  return { "Content-Type": "application/json" };
}

/**
 * @brief Parse a fetch Response, redirecting to login on 401 and throwing on other errors.
 * @param res the fetch Response to parse.
 * @return the parsed JSON body typed as T.
 */
export async function parseOrThrow<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    window.location.href = LOGIN_ROUTE;
    throw new ApiError(401, "Not authenticated");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}
