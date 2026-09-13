import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/apiClient";

/**
 * @brief Ping the backend to check whether the current session is authenticated.
 * @return true when the auth ping succeeds, false otherwise.
 */
async function fetchAuthStatus(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/ping`, { credentials: "include" });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * @brief React Query hook exposing whether the MCC session is authenticated.
 *
 * The query function never throws (it resolves to false on failure), so
 * consumers can rely on `data` being a boolean once loaded. Use `refetch`
 * to re-check after a login/logout redirect returns.
 *
 * @return useQuery result object whose data is the authentication boolean.
 */
export const useAuthStatus = () => {
  return useQuery({
    queryKey: ["auth", "status"],
    queryFn: fetchAuthStatus,
  });
};
