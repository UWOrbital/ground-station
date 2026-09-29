/**
 * In-memory store for the ARO access token.
 *
 * The access token is deliberately never persisted (no localStorage), so it
 * cannot be read back by injected scripts. After a page reload the session is
 * restored from the httpOnly refresh cookie via `refreshAccessToken` in
 * `apiClient.ts`.
 *
 * The token's expiry is not tracked here: `expires_at` is stamped by the
 * server's clock, and comparing it against a user's skewed local clock can make
 * every fresh token look expired. Instead the server is the judge — an expired
 * token gets a 401, and `authFetch` refreshes and retries.
 */

let accessToken: string | null = null;

/**
 * @brief Read the current access token.
 * @return the bearer token, or null when signed out.
 */
export function getAccessToken(): string | null {
  return accessToken;
}

/**
 * @brief Store a freshly issued access token.
 * @param token the raw JWT access token.
 */
export function setAccessToken(token: string): void {
  accessToken = token;
}

/**
 * @brief Forget the current access token (e.g. on logout or failed refresh).
 */
export function clearAccessToken(): void {
  accessToken = null;
}
