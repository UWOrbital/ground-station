import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useForgotPassword } from "@/hooks/useAuthMutations";
import { ApiError } from "@/lib/apiClient";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const { mutate, isPending, isSuccess, error } = useForgotPassword();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutate(email.trim());
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-xl bg-white text-black rounded-lg p-6 pt-6">
        <div className="flex flex-col gap-y-1 mb-8">
          <h1 className="text-lg font-medium text-center">Forgot Your Password?</h1>
          <p className="text-gray-500 text-center">
            Enter your email to request password reset instructions.
          </p>
        </div>
        {isSuccess ? (
          <p role="status" className="text-center">
            If an account exists for that email, you will receive password reset instructions.
            Please check your inbox and spam folder.
          </p>
        ) : (
          <form className="space-y-6" onSubmit={handleSubmit} aria-busy={isPending}>
            <div>
              <label htmlFor="email" className="block mb-1">
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                disabled={isPending}
                className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
                placeholder="Enter Email"
              />
            </div>
            {error && (
              <p role="alert" className="text-red-600">
                {error instanceof ApiError
                  ? error.message
                  : "Unable to request password reset instructions. Please try again."}
              </p>
            )}
            <button
              type="submit"
              disabled={isPending}
              className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? "Sending…" : "Send Reset Instructions"}
            </button>
          </form>
        )}
        <footer className="text-center mt-5 mb-5">
          <Link to="/login" className="underline">
            Back to Login
          </Link>
        </footer>
      </div>
    </div>
  );
}

export default ForgotPassword;
