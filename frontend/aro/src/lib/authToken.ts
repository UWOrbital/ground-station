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

/**
 * Holds the current access token. Use the exported {@link accessTokenStore}
 * singleton rather than constructing another store.
 */
class AccessTokenStore {
  private token: string | null = null;

  /**
   * @brief Read the current access token.
   * @return the bearer token, or null when signed out.
   */
  get(): string | null {
    return this.token;
  }

  /**
   * @brief Store a freshly issued access token.
   * @param token the raw JWT access token.
   */
  set(token: string): void {
    this.token = token;
  }

  /**
   * @brief Forget the current access token (e.g. on logout or failed refresh).
   */
  clear(): void {
    this.token = null;
  }
}

/** The app-wide access token store. */
export const accessTokenStore = new AccessTokenStore();
