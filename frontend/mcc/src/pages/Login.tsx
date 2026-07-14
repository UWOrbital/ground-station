import { API_BASE_URL } from "../utils/api/config";

/**
 * @brief Login component displaying the login page
 * @return tsx element of Login component
 */
function Login() {
  const handleLogin = () => {
    window.location.href = `${API_BASE_URL}/auth/login`;
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-md bg-gray-900/50 backdrop-blur-sm rounded-lg p-8 border border-gray-700/50">
        <h1 className="text-white text-3xl font-bold mb-6 text-center">Login</h1>
        <button
          onClick={handleLogin}
          className="w-full bg-white text-black py-2 rounded-lg hover:bg-gray-200 transition-colors cursor-pointer"
        >
          Sign in with Keycloak
        </button>
      </div>
    </div>
  );
}

export default Login;
