import { createContext, useContext, type ReactNode } from "react";
import { useAuthStatus } from "@/hooks/useAuthStatus";
import { useLogin, useLogout } from "@/hooks/useAuthMutations";
import type { AROUser } from "@/types";

interface AuthState {
  user: AROUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
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
  const { data, isLoading, refetch } = useAuthStatus();
  const loginMutation = useLogin();
  const logoutMutation = useLogout();

  const value: AuthState = {
    user: data ?? null,
    isAuthenticated: Boolean(data),
    isLoading,
    recheck: () => {
      void refetch();
    },
    login: async (email, password) => {
      await loginMutation.mutateAsync({ email, password });
    },
    logout: async () => {
      await logoutMutation.mutateAsync();
    },
  };

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
