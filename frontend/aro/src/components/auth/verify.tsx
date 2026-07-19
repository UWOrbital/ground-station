import { useNavigate } from "react-router-dom";
import { useState, type FormEvent } from "react";
import { toast } from "react-toastify";
import { useAuth } from "../../contexts/AuthContext";
import type { AROUser } from "../../types";

/**
 * @brief Verify Component showing ARO OTP verificataion form
 * @return tsx element of Verify component
 */
function Verify() {
  const { user, verifyCallsign } = useAuth();
  const navigate = useNavigate();
  const [callSign, setCallSign] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Qualification levels (A–E) — default all to false
  const [levels, setLevels] = useState({
    a: false,
    b: false,
    c: false,
    d: false,
    e: false,
  });

  const toggle = (key: keyof typeof levels) =>
    setLevels((prev) => ({ ...prev, [key]: !prev[key] }));

  const getEmail = (u: AROUser | null): string => u?.email ?? "your email";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await verifyCallsign({
        call_sign: callSign,
        qual_level_a: levels.a,
        qual_level_b: levels.b,
        qual_level_c: levels.c,
        qual_level_d: levels.d,
        qual_level_e: levels.e,
      });
      toast.success("Callsign verified successfully.");
      navigate("/");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Callsign verification failed";
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 ">
      <div className="w-full max-w-xl bg-white rounded-lg p-6 pt-6">
        <div className="flex flex-col gap-y-1 mb-8">
          <h1 className="text-black text-lg font-medium text-center">Verify Your Account</h1>
          <h2 className="text-gray-500 text-center">
            Please enter your amateur radio callsign for{" "}
            <span className="font-medium text-black">{getEmail(user)}</span> to verify your account.
          </h2>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="call-sign" className="text-black block mb-1">
              Callsign
            </label>
            <input
              type="text"
              id="call-sign"
              value={callSign}
              onChange={(e) => setCallSign(e.target.value.toUpperCase())}
              required
              className="w-full text-gray-600 px-4 py-2 rounded-lg border border-gray-600"
              placeholder="e.g. VE3ABC"
            />
          </div>

          <fieldset className="border border-gray-300 rounded-lg p-4">
            <legend className="text-black font-medium px-2">Qualification Levels</legend>
            <p className="text-gray-500 text-sm mb-3">
              Check the levels that match your amateur radio license.
            </p>
            {(["a", "b", "c", "d", "e"] as const).map((level) => (
              <label key={level} className="flex items-center gap-2 py-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={levels[level]}
                  onChange={() => toggle(level)}
                  className="h-4 w-4"
                />
                <span className="text-black">Qualification Level {level.toUpperCase()}</span>
              </label>
            ))}
          </fieldset>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-black text-white py-2 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer disabled:opacity-50"
          >
            {submitting ? "Verifying..." : "Verify Callsign"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Verify;
