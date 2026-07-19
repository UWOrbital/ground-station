import { useNavigate, Link } from "react-router-dom";
import { useState, type FormEvent } from "react";
import { toast } from "react-toastify";
import { useAuth } from "../../contexts/AuthContext";

/**
 * @brief Signup component for ARO
 * @return tsx element of Signup component
 */
function Signup() {
  const { register, loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await register({
        email,
        password,
        first_name: firstName,
        last_name: lastName || undefined,
      });
      toast.success("Account created successfully.");
      navigate("/verify");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed";
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 ">
      <div className="w-full max-w-xl bg-white rounded-lg p-6 pt-6">
        <div className="flex flex-col gap-y-1 mb-7">
          <h1 className="text-black text-lg font-medium text-center">Sign Up a New ARO Account</h1>
          <h2 className="text-gray-500 text-center">
            Enter your details below to create your account
          </h2>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="first-name" className="text-black block mb-1">
              First Name
            </label>
            <input
              type="text"
              id="first-name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter First Name"
            />
          </div>
          <div>
            <label htmlFor="last-name" className="text-black block mb-1">
              Last Name (optional)
            </label>
            <input
              type="text"
              id="last-name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Last Name"
            />
          </div>
          <div>
            <label htmlFor="email" className="text-black block mb-1">
              Email
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Email"
            />
          </div>
          <div>
            <label htmlFor="password" className="text-black block mb-1">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="At least 8 chars, 1 digit, 1 special char"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer disabled:opacity-50"
          >
            {submitting ? "Creating Account..." : "Sign Up"}
          </button>
        </form>
        <button
          type="button"
          onClick={loginWithGoogle}
          className="w-full shadow bg-white text-black py-2 rounded-lg hover:bg-gray-200 transition-colors border border-gray-700/20 mt-2 mb-5 cursor-pointer"
        >
          Continue with Google
        </button>
        <footer className="flex gap-x-2 items-center justify-center mb-5">
          <p>Already have an account?</p>
          <Link to="/login" className="underline">
            Login
          </Link>
        </footer>
      </div>
    </div>
  );
}

export default Signup;
