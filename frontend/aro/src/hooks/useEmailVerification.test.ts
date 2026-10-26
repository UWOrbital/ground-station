import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useRequestVerifyToken, useVerifyEmail } from "./useEmailVerification";
import { ApiError } from "@/lib/apiClient";
import { createQueryWrapper } from "./testUtils";

const okResponse = { ok: true, status: 202, json: async () => ({}) } as Response;

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("useRequestVerifyToken", () => {
  it("posts the email to the request-verify-token endpoint", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(okResponse);

    const { result } = renderHook(() => useRequestVerifyToken(), { wrapper: createQueryWrapper() });
    result.current.mutate("aro@example.com");

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/auth/request-verify-token");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toBe(JSON.stringify({ email: "aro@example.com" }));
  });

  it("surfaces the backend detail on failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: "Invalid email" }),
    } as Response);

    const { result } = renderHook(() => useRequestVerifyToken(), { wrapper: createQueryWrapper() });
    result.current.mutate("not-an-email");

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as ApiError).message).toBe("Invalid email");
  });
});

describe("useVerifyEmail", () => {
  it("posts the token to the verify endpoint", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: "1", email: "aro@example.com", is_verified: true }),
    } as Response);

    const { result } = renderHook(() => useVerifyEmail(), { wrapper: createQueryWrapper() });
    result.current.mutate("a-verification-token");

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/auth/verify");
    expect((init as RequestInit).method).toBe("POST");
    expect((init as RequestInit).body).toBe(JSON.stringify({ token: "a-verification-token" }));
  });

  it("surfaces a rejected token without throwing", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: "VERIFY_USER_BAD_TOKEN" }),
    } as Response);

    const { result } = renderHook(() => useVerifyEmail(), { wrapper: createQueryWrapper() });
    result.current.mutate("stale-token");

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as ApiError).status).toBe(400);
  });
});
