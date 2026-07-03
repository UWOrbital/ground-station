import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type {
  AROUser,
  CallsignPayload,
  LoginPayload,
  RegisterPayload,
  TokenResponse,
} from "../types";
import {
  getCurrentUser,
  loginUser as apiLogin,
  logoutUser as apiLogout,
  registerUser as apiRegister,
  verifyCallsign as apiVerifyCallsign,
  redirectToGoogleLogin,
} from "../services/api";

// ---- Context shape ----

interface AuthState {
  user: AROUser | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  isCallsignVerified: boolean;
}

interface AuthContextValue extends AuthState {
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  verifyCallsign: (payload: CallsignPayload) => Promise<void>;
  loginWithGoogle: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_KEY = "aro_token";

// ---- Provider ----

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Wraps the app with auth state. On mount it checks for a stored token
 * and, if present, fetches the current user from the backend.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AROUser | null>(null);
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY),
  );
  const [loading, setLoading] = useState(true);

  // Bootstrap: if a token exists, validate it by fetching the user
  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    getCurrentUser()
      .then((res) => setUser(res.data))
      .catch(() => {
        // Token is stale/invalid — clear it
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const storeAuth = useCallback(({ token: newToken }: TokenResponse) => {
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
  }, []);

  const login = useCallback(
    async (payload: LoginPayload) => {
      const res = await apiLogin(payload);
      storeAuth(res);
      const userRes = await getCurrentUser();
      setUser(userRes.data);
    },
    [storeAuth],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      const res = await apiRegister(payload);
      storeAuth(res);
      const userRes = await getCurrentUser();
      setUser(userRes.data);
    },
    [storeAuth],
  );

  const logout = useCallback(async () => {
    if (token) {
      await apiLogout(token).catch(() => {
        /* best-effort */
      });
    }
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, [token]);

  const verifyCallsign = useCallback(
    async (payload: CallsignPayload) => {
      const res = await apiVerifyCallsign(payload);
      setUser(res.data);
    },
    [],
  );

  const loginWithGoogle = useCallback(() => {
    redirectToGoogleLogin();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: !!user,
      isCallsignVerified: user?.is_callsign_verified ?? false,
      login,
      register,
      logout,
      verifyCallsign,
      loginWithGoogle,
    }),
    [user, token, loading, login, register, logout, verifyCallsign, loginWithGoogle],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Hook to access auth state and actions from any component. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
