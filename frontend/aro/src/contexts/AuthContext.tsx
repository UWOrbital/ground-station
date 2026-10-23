import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { useAuthStatus } from "@/hooks/useAuthStatus";
import { useLogin, useLogout } from "@/hooks/useAuthMutations";
import type { AROUser } from "@/types";

/**
 * Where the user stands. `loading` and `unavailable` only occur before any
 * status is known (the first check is running, or it couldn't reach the
 * backend), so guards must wait rather than treat them as signed out.
 */
export type AuthStatus = "loading" | "unavailable" | "signedIn" | "signedOut";

interface AuthState {
  status: AuthStatus;
  /** The signed-in user; non-null exactly when `status` is `signedIn`. */
  user: AROUser | null;
  recheck: () => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

/**
 * @brief Provides ARO authentication state and actions to the tree.
 *
 * Mirrors MCC's AuthProvider. ARO has no backend login/logout redirect
 * endpoints, so `login` and `logout` are exposed here as well.
 *
 * @param children the subtree that can consume auth state.
 * @return the AuthContext provider wrapping the children.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const { data, isFetching, isError, refetch } = useAuthStatus();
  const { mutateAsync: loginAsync } = useLogin();
  const { mutateAsync: logoutAsync } = useLogout();

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

  let status: AuthStatus;
  if (data) status = "signedIn";
  else if (data === null) status = "signedOut";
  else status = isError && !isFetching ? "unavailable" : "loading";

  const value = useMemo<AuthState>(
    () => ({ status, user: data ?? null, recheck, login, logout }),
    [status, data, recheck, login, logout],
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
