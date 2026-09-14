import { createContext, useContext, type ReactNode } from "react";
import { useAuthStatus } from "../hooks/useAuthStatus";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  recheck: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

/**
 * @brief Provides authentication state to the tree via the auth-status query.
 * @param children the subtree that can consume auth state.
 * @return the AuthContext provider wrapping the children.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, refetch } = useAuthStatus();

  const value: AuthState = {
    isAuthenticated: data ?? false,
    isLoading,
    recheck: () => {
      void refetch();
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * @brief Access the authentication state from the nearest AuthProvider.
 * @return the current authentication state.
 */
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
