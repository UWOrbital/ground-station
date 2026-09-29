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
 *
 * ARO endpoints authenticate with a short-lived bearer access token (held in
 * memory by `authToken.ts`) rather than a session cookie, so authenticated
 * requests should go through {@link authFetch}, which attaches the token and
 * silently rotates it using the httpOnly refresh cookie when it expires.
 */

import { clearAccessToken, getAccessToken, setAccessToken } from "@/lib/authToken";

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
 * @brief Build JSON request headers plus the bearer token when one is held.
 * @return headers object including `Authorization` if signed in.
 */
export function authHeaders(): Record<string, string> {
  const token = getAccessToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

/**
 * Body returned by `/auth/login` and `/auth/rotate_tokens`.
 */
export interface AccessTokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
}

/**
 * @brief Save an access token returned by the backend into the in-memory store.
 * @param body the parsed `/auth/login` or `/auth/rotate_tokens` response.
 */
export function storeAccessToken(body: AccessTokenResponse): void {
  setAccessToken(body.access_token);
}

/**
 * @brief Exchange the refresh cookie for a new access token.
 * @return true when a new access token was stored, false otherwise.
 */
async function rotateTokens(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/rotate_tokens`, {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) {
      clearAccessToken();
      return false;
    }
    storeAccessToken(await res.json());
    return true;
  } catch {
    clearAccessToken();
    return false;
  }
}

let refreshInFlight: Promise<boolean> | null = null;

/**
 * @brief Refresh the access token, sharing one request between concurrent callers.
 *
 * The backend treats reuse of an already-rotated refresh token as theft and
 * revokes the whole session, so two parallel rotations must never be sent.
 *
 * @return true when a new access token was stored, false otherwise.
 */
export function refreshAccessToken(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = rotateTokens().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

/**
 * Options accepted by {@link authFetch}; headers must be a plain object so they can be merged.
 */
export type AuthFetchInit = Omit<RequestInit, "headers"> & { headers?: Record<string, string> };

/**
 * @brief fetch() wrapper that attaches the bearer token and retries once after a refresh.
 * @param url the request URL.
 * @param init fetch options; headers are merged over the default auth headers.
 * @return the final Response (possibly still a 401 if the session is gone).
 */
export async function authFetch(url: string, init: AuthFetchInit = {}): Promise<Response> {
  let refreshed = false;
  if (!getAccessToken()) {
    refreshed = true;
    await refreshAccessToken();
  }

  const send = () =>
    fetch(url, { credentials: "include", ...init, headers: { ...authHeaders(), ...init.headers } });

  const sentToken = getAccessToken();
  const res = await send();
  if (res.status !== 401 || refreshed) return res;

  // The token expired. A concurrent request may already have rotated it, so
  // reuse that token rather than spending another rotation.
  const current = getAccessToken();
  if ((current !== null && current !== sentToken) || (await refreshAccessToken())) return send();
  return res;
}

/**
 * @brief Pull a human-readable message out of a FastAPI error body.
 *
 * ARO auth errors use `detail: { message, code }`, other errors use a plain
 * string `detail`.
 *
 * @param body the parsed JSON error body (may be empty).
 * @param status the HTTP status, used for the fallback message.
 * @return the best available error message.
 */
export function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message);
  }
  return `Request failed: ${status}`;
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
    throw new ApiError(res.status, errorMessage(body, res.status));
  }
  return res.json();
}
