import { Navigate, Outlet, useLocation, type Path } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import AuthGate from "./AuthGate";

/**
 * @brief Layout route rendering its child routes only for signed-out users, otherwise sending them on.
 *
 * Nest guest-only pages (login, sign-up) under `<Route element={<GuestRoute />}>`.
 * A signed-in user goes to the page they were originally heading for
 * (`state.from`, set by `ProtectedRoute`) or home, so signing in on the login
 * page returns the user there automatically.
 *
 * @return the matched child route, a loading/unavailable state, or a redirect.
 */
function GuestRoute() {
  const { status } = useAuth();
  const from = (useLocation().state as { from?: Partial<Path> } | null)?.from;

  return (
    <AuthGate>
      {status === "signedIn" ? <Navigate to={from ?? "/"} replace /> : <Outlet />}
    </AuthGate>
  );
}

export default GuestRoute;
