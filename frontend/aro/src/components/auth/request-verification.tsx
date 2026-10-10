import { useState, type FormEventHandler } from "react";
import { useNavigate } from "react-router-dom";
import { useRequestVerifyToken } from "@/hooks/useEmailVerification";
import toastService from "@/services/Toast.service";

/**
 * @brief Page where an ARO user asks the backend to email them a verification code.
 * @return tsx element of RequestVerification component
 */
function RequestVerification() {
  const [email, setEmail] = useState("");
  const navigate = useNavigate();

  const requestToken = useRequestVerifyToken();

  const handleSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    requestToken.mutate(email, {
      onSuccess: () => {
        toastService.success(`Verification code sent to ${email}`);
        navigate(`/verify?email=${encodeURIComponent(email)}`);
      },
      onError: (err) => toastService.error((err as Error).message),
    });
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 ">
      <div className="w-full max-w-xl bg-white rounded-lg p-6 pt-6">
        <div className="flex flex-col gap-y-1 mb-8">
          <h1 className="text-black text-lg font-medium text-center">Verify Your Account</h1>
          <h2 className="text-gray-500 text-center">
            Enter the email address you signed up with and we will send you a verification code
          </h2>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="request-verify-email" className="text-black block mb-1">
              Email
            </label>
            <input
              type="email"
              id="request-verify-email"
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            disabled={requestToken.isPending}
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer disabled:opacity-60"
          >
            {requestToken.isPending ? "Sending Code" : "Send Verification Code"}
          </button>
        </form>
        <footer className="flex gap-x-2 items-center justify-center mt-5 mb-5">
          <p>Already have a code?</p>
          <a href="/verify" className="underline">
            Enter Code
          </a>
        </footer>
      </div>
    </div>
  );
}

export default RequestVerification;
