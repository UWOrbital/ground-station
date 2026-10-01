import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import AuthGate from "./AuthGate";

/**
 * @brief Render children only for signed-in users, otherwise redirect to login.
 *
 * The attempted location is passed as `state.from` so the login page can
 * send the user back after signing in.
 *
 * @param children the protected page.
 * @return the page, a loading/unavailable state, or a redirect to /login.
 */
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  return (
    <AuthGate>
      {isAuthenticated ? children : <Navigate to="/login" replace state={{ from: location }} />}
    </AuthGate>
  );
}

export default ProtectedRoute;
