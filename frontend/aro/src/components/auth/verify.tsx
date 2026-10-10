import { useState, type FormEventHandler } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useRequestVerifyToken, useVerifyEmail } from "@/hooks/useEmailVerification";
import toastService from "@/services/Toast.service";

/**
 * @brief Page where an ARO user submits the verification code emailed to them.
 * @return tsx element of Verify component
 */
function Verify() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Set when the user arrives from the emailed link, which carries the token.
  const emailedToken = searchParams.get("token") ?? "";
  const email = searchParams.get("email");

  const [token, setToken] = useState(emailedToken);
  const requestToken = useRequestVerifyToken();
  const verifyEmail = useVerifyEmail();

  const handleSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    verifyEmail.mutate(token, {
      onSuccess: () => {
        toastService.success("Your email address has been verified");
        navigate("/login");
      },
      onError: (err) => toastService.error((err as Error).message),
    });
  };

  const handleResend = () => {
    // Without an email on the URL there is nothing to resend to, so ask for it.
    if (!email) {
      navigate("/verify/request");
      return;
    }

    requestToken.mutate(email, {
      onSuccess: () => toastService.success(`Verification code sent to ${email}`),
      onError: (err) => toastService.error((err as Error).message),
    });
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 ">
      <div className="w-full max-w-xl bg-white rounded-lg p-6 pt-6">
        <div className="flex flex-col gap-y-1 mb-8">
          <h1 className="text-black text-lg font-medium text-center">Verify Your Account</h1>
          <h2 className="text-gray-500 text-center">
            {email
              ? `Please Enter the verification code that we sent to ${email} in order to verify your account`
              : "Please Enter the verification code that we sent to you in order to verify your account"}
          </h2>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="otp-code" className="text-black block mb-1">
              OTP Verification Code
            </label>
            <input
              type="text"
              id="otp-code"
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Verification Code"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            disabled={verifyEmail.isPending}
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer disabled:opacity-60"
          >
            {verifyEmail.isPending ? "Confirming" : "Confirm Code"}
          </button>
        </form>
        <button
          type="button"
          onClick={handleResend}
          disabled={requestToken.isPending}
          className="w-full shadow bg-white text-black py-2 rounded-lg hover:bg-gray-200 transition-colors border border-gray-700/20 mt-2 mb-15 cursor-pointer disabled:opacity-60"
        >
          {requestToken.isPending ? "Sending Code" : "Resend Code"}
        </button>
      </div>
    </div>
  );
}

export default Verify;
