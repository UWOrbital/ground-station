import { useMutation, useQueryClient } from "@tanstack/react-query";
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
 * Fields submitted from the ARO registration form.
 */
export interface RegisterData {
  first_name: string;
  last_name?: string;
  email: string;
  password: string;
  call_sign: string;
  phone_number?: string;
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

/**
 * @brief Register a new ARO account.
 *
 * Hits the fastapi-users `POST /auth/register` route, which expects a JSON
 * body. Optional fields are omitted when empty so the backend validators
 * (e.g. the phone-number parser) don't reject blank strings.
 *
 * @param data the registration fields collected from the signup form.
 * @throws ApiError when the backend rejects the registration.
 */
async function postRegister(data: RegisterData): Promise<void> {
  const body: Record<string, string> = {
    first_name: data.first_name,
    email: data.email,
    password: data.password,
    call_sign: data.call_sign,
  };
  if (data.last_name) body.last_name = data.last_name;
  if (data.phone_number) body.phone_number = data.phone_number;

  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    credentials: "include",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new ApiError(res.status, errorMessage(errBody, res.status));
  }
}

/**
 * @brief Mutation hook that registers a new ARO account.
 * @return useMutation result object; call `mutateAsync(data)`.
 */
export const useRegister = () => {
  return useMutation({ mutationFn: postRegister });
};
