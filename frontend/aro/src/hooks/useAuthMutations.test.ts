import { describe, it, expect, vi, beforeEach } from "vitest";
import { useRegister } from "@/hooks/useAuthMutations";
import { renderHook } from "@testing-library/react";
import { createQueryWrapper } from "./testUtils";

describe("useRegister", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("omits empty optional fields from the request body", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: "1" }), { status: 201 }),
    );
    const { result } = renderHook(() => useRegister(), { wrapper: createQueryWrapper() });

    // last name and phone number intentionally absent
    await result.current.mutateAsync({
      first_name: "Alice",
      email: "alice@example.com",
      password: "blah2bla",
      call_sign: "VA3ABC",
    });

    const body = JSON.parse((fetchSpy.mock.calls[0][1] as RequestInit).body as string);
    expect(body).not.toHaveProperty("phone_number");
    expect(body).not.toHaveProperty("last_name");
    expect(body.call_sign).toBe("VA3ABC");
  });

  it("posts to the register endpoint and includes optional fields when present", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: "1" }), { status: 201 }),
    );
    const { result } = renderHook(() => useRegister(), { wrapper: createQueryWrapper() });

    await result.current.mutateAsync({
      first_name: "Alice",
      last_name: "Smith",
      email: "alice@example.com",
      password: "blah2bla",
      call_sign: "VA3ABC",
      phone_number: "+15195550123",
    });

    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/auth/register");
    expect((init as RequestInit).method).toBe("POST");
    const body = JSON.parse((init as RequestInit).body as string);
    expect(body.last_name).toBe("Smith");
    expect(body.phone_number).toBe("+15195550123");
  });

  it("surfaces an ApiError on a non-ok response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "REGISTER_USER_ALREADY_EXISTS" }), { status: 400 }),
    );
    const { result } = renderHook(() => useRegister(), { wrapper: createQueryWrapper() });
    await expect(
      result.current.mutateAsync({
        first_name: "Alice",
        email: "alice@example.com",
        password: "blah2bla",
        call_sign: "VA3ABC",
      }),
    ).rejects.toThrow();
  });
});
