import { useMutation, useQueryClient } from "@tanstack/react-query";
import { API_BASE_URL, ApiError, errorMessage, storeAccessToken } from "@/lib/apiClient";
import { accessTokenStore } from "@/lib/authToken";
import { AUTH_STATUS_QUERY_KEY } from "@/hooks/useAuthStatus";

/**
 * Credentials submitted from the ARO login form.
 */
export interface LoginCredentials {
  email: string;
  password: string;
}

/**
 * @brief Log in with email and password, storing the returned access token.
 *
 * Uses plain fetch rather than `parseOrThrow` so a 401 (bad credentials)
 * surfaces as an error instead of redirecting back to the login page.
 *
 * @param credentials the email and password to authenticate with.
 * @throws ApiError when the backend rejects the credentials.
 */
async function postLogin({ email, password }: LoginCredentials): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    credentials: "include",
    // The backend uses OAuth2PasswordRequestForm, which expects `username`.
    body: new URLSearchParams({ username: email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, errorMessage(body, res.status));
  }
  storeAccessToken(await res.json());
}

/**
 * @brief Revoke the refresh cookie on the backend and drop the local access token.
 * @throws ApiError when the backend logout request fails.
 */
async function postLogout(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) throw new ApiError(res.status, `Logout failed: ${res.status}`);
  } finally {
    accessTokenStore.clear();
  }
}

/**
 * @brief Mutation hook logging the user in and refreshing the auth status.
 * @return useMutation result object; call `mutateAsync(credentials)`.
 */
export const useLogin = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: postLogin,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: AUTH_STATUS_QUERY_KEY }),
  });
};

/**
 * @brief Mutation hook logging the user out and clearing every cached user query.
 * @return useMutation result object; call `mutateAsync()`.
 */
export const useLogout = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: postLogout,
    onSettled: () => {
      // Drop the previous user's data so the next user never sees it.
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== "auth" });
      queryClient.setQueryData(AUTH_STATUS_QUERY_KEY, null);
    },
  });
};
