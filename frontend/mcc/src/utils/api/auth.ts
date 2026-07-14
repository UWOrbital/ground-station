import { API_BASE_URL } from "./config";

export async function checkAuth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/ping`, { credentials: "include" });
    return res.ok;
  } catch {
    return false;
  }
}
