import { describe, it, expect, vi, afterEach } from "vitest";
import { API_BASE_URL, ApiError, jsonHeaders, parseOrThrow } from "@/lib/apiClient";

const response = (status: number, json: () => Promise<unknown>) =>
  ({ status, ok: status >= 200 && status < 300, json }) as Response;

describe("parseOrThrow", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the parsed body on success", async () => {
    await expect(parseOrThrow(response(200, async () => ({ data: [1] })))).resolves.toEqual({
      data: [1],
    });
  });

  it("redirects to login and throws on 401", async () => {
    vi.stubGlobal("location", { href: "" });
    await expect(parseOrThrow(response(401, async () => ({})))).rejects.toMatchObject({
      status: 401,
      message: "Not authenticated",
    });
    expect(window.location.href).toBe(`${API_BASE_URL}/auth/login`);
  });

  it("throws an ApiError carrying the backend detail and status", async () => {
    const err = parseOrThrow(response(404, async () => ({ detail: "Session not found" })));
    await expect(err).rejects.toBeInstanceOf(ApiError);
    await expect(err).rejects.toMatchObject({ status: 404, message: "Session not found" });
  });

  it("falls back to a generic message when the error body has no detail or isn't JSON", async () => {
    await expect(parseOrThrow(response(500, async () => ({})))).rejects.toThrow(
      "Request failed: 500",
    );
    await expect(
      parseOrThrow(response(502, () => Promise.reject(new SyntaxError("bad json")))),
    ).rejects.toThrow("Request failed: 502");
  });
});

describe("jsonHeaders", () => {
  it("sends JSON", () => {
    expect(jsonHeaders()).toEqual({ "Content-Type": "application/json" });
  });
});
