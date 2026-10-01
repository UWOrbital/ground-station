import type { ReactNode } from "react";
import { useAuth } from "@/contexts/AuthContext";

/**
 * @brief Hold back route content until the auth status is known.
 *
 * Shows a loading message while the first auth check runs, and a retry prompt
 * when the backend couldn't be reached, so route guards never decide where to
 * send the user before the status is known.
 *
 * @param children the route guard to render once the status is known.
 * @return the loading or unavailable state, or the children.
 */
function AuthGate({ children }: { children: ReactNode }) {
  const { isLoading, isUnavailable, recheck } = useAuth();

  if (isLoading) return <div className="text-white text-center mt-20">Loading...</div>;
  if (isUnavailable) {
    return (
      <div className="text-white text-center mt-20 space-y-4">
        <p>Can&apos;t reach the ARO server right now.</p>
        <button
          type="button"
          onClick={recheck}
          className="border-1 border-white rounded-xl p-1 px-3 hover:bg-white hover:text-black"
        >
          Retry
        </button>
      </div>
    );
  }

  return <>{children}</>;
}

export default AuthGate;
