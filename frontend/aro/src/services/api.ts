/**
 * @brief Base API configuration for ARO frontend
 */

import type {
  CallsignPayload,
  LoginPayload,
  RegisterPayload,
  TokenResponse,
  UserResponse,
} from "../types";

const ARO_API_BASE_URL = import.meta.env.VITE_ARO_API_BASE_URL ?? "/api/v1/aro";

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

/**
 * @brief Get the auth token from localStorage
 * @return the stored auth token value, or null if not present
 */
export function getAuthToken(): string | null {
  return localStorage.getItem("aro_token");
}

/**
 * @brief Thin wrapper around fetch that prepends the ARO API base URL,
 *        serializes JSON bodies, and parses errors consistently.
 */
async function request<T>(path: string, method: HttpMethod = "GET", body?: unknown): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const token = getAuthToken();
  if (token) {
    headers["X-Auth-Token"] = token;
  }

  const config: RequestInit = {
    method,
    headers,
  };

  if (body !== undefined) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${ARO_API_BASE_URL}${path}`, config);

  if (!response.ok) {
    let detail = `Request failed: ${response.statusText}`;
    try {
      const err = await response.json();
      detail = err.detail || JSON.stringify(err);
    } catch {
      // response body is not JSON — stick with status text
    }
    const hint = response.status === 404
      ? " - is the backend running the zaid/direct-requests-backend branch?"
      : "";
    throw new Error(`${detail}${hint}`);
  }

  return response.json() as Promise<T>;
}

/**
 * @brief Perform an authenticated GET request to the ARO API
 * @param path the API path relative to the base URL
 * @return parsed JSON response
 */
export async function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, "GET");
}

/**
 * @brief Perform an authenticated POST request to the ARO API
 * @param path the API path relative to the base URL
 * @param body the JSON request body
 * @return parsed JSON response
 */
export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, "POST", body);
}

// ---- Auth endpoints ----

/** Register a new user with email and password. Returns a token on success. */
export function registerUser(payload: RegisterPayload): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/register", "POST", payload);
}

/** Log in with email and password. Returns a token on success. */
export function loginUser(payload: LoginPayload): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", "POST", payload);
}

/** Fetch the currently authenticated user. Token is passed as a query param
 *  to match the backend's `get_current_user(token: str)` dependency signature. */
export function getCurrentUser(): Promise<UserResponse> {
  const token = getAuthToken();
  return request<UserResponse>(`/auth/current_user?token=${token || ""}`, "GET");
}

/** Log out by invalidating the token on the server. */
export function logoutUser(token: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/auth/logout/${token}`, "POST");
}

/** Redirect the browser to the Google OAuth flow. */
export function redirectToGoogleLogin(): void {
  window.location.href = `${ARO_API_BASE_URL}/auth/google/login`;
}

/** Verify a user's amateur radio callsign (second factor). */
export function verifyCallsign(payload: CallsignPayload): Promise<UserResponse> {
  const token = getAuthToken();
  return request<UserResponse>(`/auth/callsign_callback?token=${token || ""}`, "POST", payload);
}
