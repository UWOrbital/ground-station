import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL, authFetch, parseOrThrow, refreshAccessToken } from "@/lib/apiClient";
import { accessTokenStore } from "@/lib/authToken";
import type { AROUser } from "@/types";

export const AUTH_STATUS_QUERY_KEY = ["auth", "status"] as const;

/**
 * How long a resolved auth status is trusted before a window refocus re-checks
 * it. Login and logout update the status directly and any API 401 signs the
 * user out, so this only bounds how long a session revoked elsewhere goes
 * unnoticed while the user makes no API calls.
 */
const AUTH_STATUS_STALE_TIME_MS = 5 * 60 * 1000;

/**
 * @brief Resolve the currently signed-in ARO user, if any.
 *
 * With no access token in memory (e.g. after a reload) this first tries to
 * restore the session from the refresh cookie, and skips the user lookup
 * entirely when that fails.
 *
 * Only a 401 means "signed out". Outages throw, so React Query keeps the last
 * known user instead of signing them out over a network blip.
 *
 * @return the signed-in user, or null when there is no valid session.
 * @throws ApiError or a network error when the backend can't be reached.
 */
async function fetchCurrentUser(): Promise<AROUser | null> {
  if (!accessTokenStore.get() && !(await refreshAccessToken())) return null;
  const res = await authFetch(`${API_BASE_URL}/auth/get_current_user`);
  if (res.status === 401) {
    // e.g. an inactive account, whose refresh still succeeds; drop the token it got.
    accessTokenStore.clear();
    return null;
  }
  return parseOrThrow<AROUser>(res);
}

/**
 * @brief React Query hook exposing the signed-in ARO user.
 *
 * Mirrors MCC's `useAuthStatus`, but resolves to the user (or null) instead of
 * a boolean because ARO pages need fields like `is_callsign_verified`. `data`
 * is `AROUser | null` once loaded; it stays undefined only if the very first
 * check fails with an outage.
 *
 * A failed check is not retried automatically: the UI offers a retry, and
 * React Query re-checks on refocus and reconnect anyway. It also runs while
 * the browser reports offline, so an outage surfaces as an error instead of
 * a fetch that stays paused.
 *
 * @return useQuery result object whose data is the signed-in user or null.
 */
export const useAuthStatus = () => {
  return useQuery({
    queryKey: AUTH_STATUS_QUERY_KEY,
    queryFn: fetchCurrentUser,
    staleTime: AUTH_STATUS_STALE_TIME_MS,
    retry: false,
    networkMode: "always",
  });
};
