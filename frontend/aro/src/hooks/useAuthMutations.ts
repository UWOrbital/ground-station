import { type Query, type QueryClient, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  API_BASE_URL,
  ApiError,
  errorMessage,
  jsonHeaders,
  storeAccessToken,
} from "@/lib/apiClient";
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
 * surfaces the backend's message instead of being treated as an expired session.
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
 * @brief Whether a cached query holds signed-in user data (anything but auth state).
 * @param query the cached query to check.
 * @return true for every query outside the `auth` key namespace.
 */
const isUserQuery = (query: Query): boolean => query.queryKey[0] !== "auth";

/**
 * @brief Mutation hook logging the user in and refreshing the auth status.
 *
 * Drops any data a previous user left in the cache first, so the new user
 * never sees it.
 *
 * @return useMutation result object; call `mutateAsync(credentials)`.
 */
export const useLogin = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: postLogin,
    onSuccess: () => {
      queryClient.removeQueries({ predicate: isUserQuery });
      return queryClient.invalidateQueries({ queryKey: AUTH_STATUS_QUERY_KEY });
    },
  });
};

/**
 * @brief Mark the user signed out and drop the cached user data no page is using.
 *
 * Shared by logout and the API 401 handler. Cancels any in-flight auth check so
 * it can't sign the user back in. Keeps queries a mounted page uses, since
 * removing one mid-fetch leaves that page loading forever; login clears those.
 *
 * @param queryClient the app's React Query client.
 */
export function clearSession(queryClient: QueryClient): void {
  void queryClient.cancelQueries({ queryKey: AUTH_STATUS_QUERY_KEY });
  queryClient.removeQueries({ predicate: isUserQuery, type: "inactive" });
  queryClient.setQueryData(AUTH_STATUS_QUERY_KEY, null);
}

/**
 * @brief Mutation hook logging the user out and clearing every cached user query.
 * @return useMutation result object; call `mutateAsync()`.
 */
export const useLogout = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: postLogout,
    onSettled: () => clearSession(queryClient),
  });
};

async function postForgotPassword(email: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, errorMessage(body, res.status));
  }
}

export const useForgotPassword = () => useMutation({ mutationFn: postForgotPassword });
