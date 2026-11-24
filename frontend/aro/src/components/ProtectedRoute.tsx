import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import AuthGate from "./AuthGate";

/**
 * @brief Layout route rendering its child routes only for signed-in users, otherwise redirecting to login.
 *
 * Nest protected pages under `<Route element={<ProtectedRoute />}>`. The
 * attempted location is passed as `state.from` so the login page can send the
 * user back after signing in.
 *
 * @return the matched child route, a loading/unavailable state, or a redirect to /login.
 */
function ProtectedRoute() {
  const { status } = useAuth();
  const location = useLocation();

  return (
    <AuthGate>
      {status === "signedIn" ? (
        <Outlet />
      ) : (
        <Navigate to="/login" replace state={{ from: location }} />
      )}
    </AuthGate>
  );
}

export default ProtectedRoute;
