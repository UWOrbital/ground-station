import { useQuery } from "@tanstack/react-query";
import {
  API_BASE_URL,
  ApiError,
  authFetch,
  errorMessage,
  refreshAccessToken,
} from "@/lib/apiClient";
import { accessTokenStore } from "@/lib/authToken";
import type { AROUser } from "@/types";

export const AUTH_STATUS_QUERY_KEY = ["auth", "status"] as const;

/**
 * How long a resolved auth status is trusted before a window refocus re-checks
 * it. Login, logout and API 401s update the status directly, so this only
 * bounds how long a session revoked elsewhere goes unnoticed.
 */
export const AUTH_STATUS_STALE_TIME_MS = 5 * 60 * 1000;

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
  if (res.status === 401) return null;
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, errorMessage(body, res.status));
  }
  return (await res.json()) as AROUser;
}

/**
 * @brief React Query hook exposing the signed-in ARO user.
 *
 * Mirrors MCC's `useAuthStatus`, but resolves to the user (or null) instead of
 * a boolean because ARO pages need fields like `is_callsign_verified`. `data`
 * is `AROUser | null` once loaded; it stays undefined only if the very first
 * check fails with an outage.
 *
 * @return useQuery result object whose data is the signed-in user or null.
 */
export const useAuthStatus = () => {
  return useQuery({
    queryKey: AUTH_STATUS_QUERY_KEY,
    queryFn: fetchCurrentUser,
    staleTime: AUTH_STATUS_STALE_TIME_MS,
  });
};
