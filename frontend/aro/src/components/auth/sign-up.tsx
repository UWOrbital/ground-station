import { useState, type FormEventHandler } from "react";
import { useNavigate } from "react-router-dom";
import { useRegister } from "@/hooks/useAuthMutations";
import toastService from "@/services/Toast.service";

/**
 * @brief Signup component for ARO
 * @return tsx element of Signup component
 */
function Signup() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [callSign, setCallSign] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");

  const register = useRegister();
  const navigate = useNavigate();

  const handleSubmit: FormEventHandler<HTMLFormElement> = async (event) => {
    event.preventDefault();
    register.mutate(
      {
        first_name: firstName,
        last_name: lastName || undefined,
        call_sign: callSign,
        email,
        password,
        phone_number: phoneNumber || undefined,
      },
      {
        onSuccess: () => {
          toastService.success("Account created. Please verify your email.");
          navigate(`/verify/request`);
        },
        onError: (err) => toastService.error((err as Error).message),
      },
    );
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 ">
      <div className="w-full max-w-xl bg-white rounded-lg p-6 pt-6">
        <div className="flex flex-col gap-y-1 mb-7">
          <h1 className="text-black text-lg font-medium text-center">Sign Up a New Aro Account</h1>
          <h2 className="text-gray-500 text-center">
            Enter your email below to login to your account
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
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter First Name"
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="last-name" className="text-black block mb-1">
              Last Name
            </label>
            <input
              type="text"
              id="last-name"
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Last Name"
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="call-sign" className="text-black block mb-1">
              Call Sign
            </label>
            <input
              type="text"
              id="call-sign"
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Call Sign"
              value={callSign}
              onChange={(event) => setCallSign(event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="email" className="text-black block mb-1">
              Email
            </label>
            <input
              type="email"
              id="email"
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="text-black block mb-1">
              Password
            </label>
            <input
              type="password"
              id="password"
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="phone-number" className="text-black block mb-1">
              Phone Number
            </label>
            <input
              type="tel"
              id="phone-number"
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="Enter Phone Number"
              value={phoneNumber}
              onChange={(event) => setPhoneNumber(event.target.value)}
            />
          </div>
          <button
            type="submit"
            disabled={register.isPending}
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer"
          >
            {register.isPending ? "Creating Account" : "Sign Up"}
          </button>
        </form>
        <button
          type="button"
          className="w-full shadow bg-white text-black py-2 rounded-lg hover:bg-gray-200 transition-colors border border-gray-700/20 mt-2 mb-15 cursor-pointer"
        >
          Continue with Google
        </button>
        <footer className="flex gap-x-2 items-center justify-center mt-5 mb-5">
          <p>Already have an Account?</p>
          <a href="/login" className="underline">
            Login
          </a>
        </footer>
      </div>
    </div>
  );
}

export default Signup;
