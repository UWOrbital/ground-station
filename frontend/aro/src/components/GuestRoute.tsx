import type { ReactNode } from "react";
import { Navigate, useLocation, type Path } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import AuthGate from "./AuthGate";

/**
 * @brief Render children only for signed-out users, otherwise send them on.
 *
 * Used for login and sign-up. A signed-in user goes to the page they were
 * originally heading for (`state.from`, set by `ProtectedRoute`) or home, so
 * signing in on the login page returns the user there automatically.
 *
 * @param children the guest-only page.
 * @return the page, a loading/unavailable state, or a redirect.
 */
function GuestRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const from = (useLocation().state as { from?: Partial<Path> } | null)?.from;

  return <AuthGate>{isAuthenticated ? <Navigate to={from ?? "/"} replace /> : children}</AuthGate>;
}

export default GuestRoute;
