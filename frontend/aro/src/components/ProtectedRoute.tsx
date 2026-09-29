import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

/**
 * @brief Render children only for signed-in users, otherwise redirect to login.
 *
 * The attempted location is passed as `state.from` so the login page can
 * send the user back after signing in.
 *
 * @param children the protected page.
 * @return the page, a loading state, or a redirect to /login.
 */
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <div className="text-white text-center mt-20">Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />;

  return <>{children}</>;
}

export default ProtectedRoute;
