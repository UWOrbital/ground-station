import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { checkAuth } from "../utils/api/auth";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  recheck: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const recheck = () => {
    setIsLoading(true);
    checkAuth()
      .then(setIsAuthenticated)
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    recheck();
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, recheck }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
