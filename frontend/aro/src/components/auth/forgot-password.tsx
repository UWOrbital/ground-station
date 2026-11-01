import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useForgotPassword } from "@/hooks/useAuthMutations";
import { ApiError } from "@/lib/apiClient";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sentTo, setSentTo] = useState<string | null>(null);
  const { mutate, isPending, error } = useForgotPassword();

  function send(address: string) {
    mutate(address, { onSuccess: () => setSentTo(address) });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    send(email.trim());
  }

  const errorMessage = error && (
    <p role="alert" className="text-red-600">
      {error instanceof ApiError
        ? error.message
        : "Unable to request password reset instructions. Please try again."}
    </p>
  );

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-xl bg-white text-black rounded-lg p-6 pt-6">
        <div className="flex flex-col gap-y-1 mb-8">
          <h1 className="text-lg font-medium text-center">Reset your password</h1>
          <p className="text-gray-500 text-center">
            Enter your email and we&apos;ll send you a link to reset your password.
          </p>
        </div>
        {sentTo ? (
          <div className="space-y-4">
            <p role="status" className="text-center">
              We&apos;ve sent a link to reset your password to {sentTo}.
            </p>
            <p className="text-sm text-gray-500 text-center">
              The link will expire in 1 hour. Check your spam folder if you don&apos;t see it.
            </p>
            {errorMessage}
            <button
              type="button"
              onClick={() => send(sentTo)}
              disabled={isPending}
              className="w-full border border-black py-2 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? "Sending…" : "Resend link"}
            </button>
          </div>
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
                placeholder="name@example.com"
              />
            </div>
            {errorMessage}
            <button
              type="submit"
              disabled={isPending}
              className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? "Sending…" : "Send reset link"}
            </button>
          </form>
        )}
        <footer className="text-center mt-5 mb-5">
          <Link to="/login" className="underline">
            Back to login
          </Link>
        </footer>
      </div>
    </div>
  );
}

export default ForgotPassword;
