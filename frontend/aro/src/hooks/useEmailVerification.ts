import { useMutation } from "@tanstack/react-query";
import { API_BASE_URL, jsonHeaders, throwIfError } from "@/lib/apiClient";

/**
 * @brief Ask the backend to email a verification code to an ARO user.
 * @param email address of the ARO account to verify.
 * @return resolves once the backend has accepted the request; the backend
 *     answers 202 whether or not the address belongs to an account.
 */
async function requestVerifyToken(email: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/auth/request-verify-token`, {
    method: "POST",
    credentials: "include",
    headers: jsonHeaders(),
    body: JSON.stringify({ email }),
  });
  await throwIfError(res);
}

/**
 * @brief Confirm an ARO user's email address with the code they were sent.
 * @param token verification token emailed by the backend.
 * @return resolves once the account is marked verified.
 */
async function verifyEmail(token: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/auth/verify`, {
    method: "POST",
    credentials: "include",
    headers: jsonHeaders(),
    body: JSON.stringify({ token }),
  });
  await throwIfError(res);
}

/**
 * @brief React Query mutation that requests a fresh verification code by email.
 * @return useMutation result object for the request-verify-token call.
 */
export const useRequestVerifyToken = () => {
  return useMutation({ mutationFn: requestVerifyToken });
};

/**
 * @brief React Query mutation that verifies an ARO user's email address.
 * @return useMutation result object for the verify call.
 */
export const useVerifyEmail = () => {
  return useMutation({ mutationFn: verifyEmail });
};
