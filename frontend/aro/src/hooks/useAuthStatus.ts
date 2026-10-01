import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL, authFetch, refreshAccessToken } from "@/lib/apiClient";
import { accessTokenStore } from "@/lib/authToken";
import type { AROUser } from "@/types";

export const AUTH_STATUS_QUERY_KEY = ["auth", "status"] as const;

/**
 * @brief Resolve the currently signed-in ARO user, if any.
 *
 * With no access token in memory (e.g. after a reload) this first tries to
 * restore the session from the refresh cookie, and skips the user lookup
 * entirely when that fails.
 *
 * @return the signed-in user, or null when signed out or on any failure.
 */
async function fetchCurrentUser(): Promise<AROUser | null> {
  try {
    if (!accessTokenStore.get() && !(await refreshAccessToken())) return null;
    const res = await authFetch(`${API_BASE_URL}/auth/get_current_user`);
    if (!res.ok) return null;
    return (await res.json()) as AROUser;
  } catch {
    return null;
  }
}

/**
 * @brief React Query hook exposing the signed-in ARO user.
 *
 * Mirrors MCC's `useAuthStatus`, but resolves to the user (or null) instead of
 * a boolean because ARO pages need fields like `is_callsign_verified`. The
 * query function never throws, so `data` is `AROUser | null` once loaded.
 *
 * @return useQuery result object whose data is the signed-in user or null.
 */
export const useAuthStatus = () => {
  return useQuery({
    queryKey: AUTH_STATUS_QUERY_KEY,
    queryFn: fetchCurrentUser,
  });
};
