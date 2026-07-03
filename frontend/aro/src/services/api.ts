import type {
  CallsignPayload,
  LoginPayload,
  RegisterPayload,
  TokenResponse,
  UserResponse,
} from "../types";

const BASE_URL = "/api/v1/aro";

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

/**
 * Thin wrapper around fetch that prepends the ARO API base URL,
 * serializes JSON bodies, and parses errors consistently.
 */
async function request<T>(path: string, method: HttpMethod = "GET", body?: unknown): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const config: RequestInit = {
    method,
    headers,
  };

  if (body !== undefined) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${BASE_URL}${path}`, config);

  if (!response.ok) {
    let detail = `Request failed: ${response.statusText}`;
    try {
      const err = await response.json();
      detail = err.detail || JSON.stringify(err);
    } catch {
      // response body is not JSON — stick with status text
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
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
  const token = localStorage.getItem("aro_token");
  return request<UserResponse>(`/auth/current_user?token=${token || ""}`, "GET");
}

/** Log out by invalidating the token on the server. */
export function logoutUser(token: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/auth/logout/${token}`, "POST");
}

/** Redirect the browser to the Google OAuth flow. */
export function redirectToGoogleLogin(): void {
  window.location.href = `${BASE_URL}/auth/google/login`;
}

/** Verify a user's amateur radio callsign (second factor). */
export function verifyCallsign(payload: CallsignPayload): Promise<UserResponse> {
  const token = localStorage.getItem("aro_token");
  return request<UserResponse>(`/auth/callsign_callback?token=${token || ""}`, "POST", payload);
}
