/**
 * In-memory store for the ARO access token.
 *
 * The access token is deliberately never persisted (no localStorage), so it
 * cannot be read back by injected scripts. After a page reload the session is
 * restored from the httpOnly refresh cookie via `refreshAccessToken` in
 * `apiClient.ts`.
 */

// Treat the token as expired slightly early so it never lapses mid-request.
const EXPIRY_SKEW_MS = 10_000;

let accessToken: string | null = null;
let expiresAtMs = 0;

/**
 * @brief Read the current access token if it is still valid.
 * @return the bearer token, or null when absent or about to expire.
 */
export function getAccessToken(): string | null {
  if (accessToken && Date.now() < expiresAtMs - EXPIRY_SKEW_MS) return accessToken;
  return null;
}

/**
 * @brief Store a freshly issued access token.
 * @param token the raw JWT access token.
 * @param expiresAt when the backend says the token expires.
 */
export function setAccessToken(token: string, expiresAt: Date): void {
  accessToken = token;
  expiresAtMs = expiresAt.getTime();
}

/**
 * @brief Forget the current access token (e.g. on logout or failed refresh).
 */
export function clearAccessToken(): void {
  accessToken = null;
  expiresAtMs = 0;
}
