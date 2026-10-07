import { createContext, useCallback, useContext, useEffect, useMemo, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStatus } from "@/hooks/useAuthStatus";
import { clearSession, useLogin, useLogout } from "@/hooks/useAuthMutations";
import { setUnauthorizedHandler } from "@/lib/apiClient";
import type { AROUser } from "@/types";

interface AuthState {
  user: AROUser | null;
  isAuthenticated: boolean;
  /** True until the first auth check settles, including retries after an outage. */
  isLoading: boolean;
  /** True when the backend couldn't be reached and no auth status is known yet. */
  isUnavailable: boolean;
  recheck: () => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

/**
 * @brief Provides ARO authentication state and actions to the tree.
 *
 * Mirrors MCC's AuthProvider. ARO has no backend login/logout redirect
 * endpoints, so `login` and `logout` are exposed here as well. It also signs
 * the user out when any API call reports a 401, so `ProtectedRoute` handles
 * the redirect.
 *
 * @param children the subtree that can consume auth state.
 * @return the AuthContext provider wrapping the children.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const { data, isPending, isFetching, isError, refetch } = useAuthStatus();
  const { mutateAsync: loginAsync } = useLogin();
  const { mutateAsync: logoutAsync } = useLogout();

  useEffect(() => {
    setUnauthorizedHandler(() => clearSession(queryClient));
    return () => setUnauthorizedHandler(null);
  }, [queryClient]);

  const recheck = useCallback(() => {
    void refetch();
  }, [refetch]);
  const login = useCallback(
    async (email: string, password: string) => {
      await loginAsync({ email, password });
    },
    [loginAsync],
  );
  const logout = useCallback(async () => {
    await logoutAsync();
  }, [logoutAsync]);

  const noStatusYet = data === undefined;
  const isLoading = noStatusYet && (isPending || isFetching);
  const isUnavailable = noStatusYet && isError && !isFetching;

  const value = useMemo<AuthState>(
    () => ({
      user: data ?? null,
      isAuthenticated: Boolean(data),
      isLoading,
      isUnavailable,
      recheck,
      login,
      logout,
    }),
    [data, isLoading, isUnavailable, recheck, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * @brief Access the authentication state from the nearest AuthProvider.
 * @return the current authentication state and actions.
 */
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
