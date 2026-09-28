import { useState, type FormEvent } from "react";
import { useLocation, useNavigate, type Location } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError } from "@/lib/apiClient";
import toastService from "@/services/Toast.service";

/**
 * @brief Login component for ARO
 * @return tsx element of Login component
 */
function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ProtectedRoute passes the page the user was trying to reach.
  const from = (location.state as { from?: Location } | null)?.from?.pathname ?? "/";

  /**
   * @brief Submit the credentials and return to the originally requested page.
   * @param event the form submit event.
   */
  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      toastService.error(err instanceof ApiError ? err.message : "Login failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-xl bg-white rounded-lg p-6 pt-6">
        <div className="flex flex-col gap-y-1 mb-8">
          <h1 className="text-black text-lg font-medium text-center">Login to your ARO Account</h1>
          <h2 className="text-gray-500 text-center">
            Enter your email below to login to your account
          </h2>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="text-black block mb-1">
              Email
            </label>
            <input
              type="text"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Email"
            />
          </div>
          <div>
            <div className="flex justify-between">
              <label htmlFor="password" className="text-black block mb-1">
                Password
              </label>
              <a className="hover:underline cursor-pointer">Forgot Your Pasword? </a>
            </div>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Password"
            />
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isSubmitting ? "Logging in..." : "Login"}
          </button>
        </form>
        <button
          type="button"
          className="w-full shadow bg-white text-black py-2 rounded-lg hover:bg-gray-200 transition-colors border border-gray-700/20 mt-2 cursor-pointer"
        >
          Login with Google
        </button>

        <footer className="flex gap-x-2 items-center justify-center mt-5 mb-5">
          <p>Don&apos;t have an Account?</p>
          <a href="/sign-up" className="underline">
            Sign Up
          </a>
        </footer>
      </div>
    </div>
  );
}

export default Login;
