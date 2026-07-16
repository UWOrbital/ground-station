import { API_BASE_URL } from "./config";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function jsonHeaders(): HeadersInit {
  return { "Content-Type": "application/json" };
}

export async function parseOrThrow<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    window.location.href = `${API_BASE_URL}/auth/login`;
    throw new ApiError(401, "Not authenticated");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function checkAuth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/ping`, { credentials: "include" });
    return res.ok;
  } catch {
    return false;
  }
}
