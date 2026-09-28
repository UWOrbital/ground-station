import { describe, it, expect, beforeEach } from "vitest";
import { clearAccessToken, getAccessToken, setAccessToken } from "./authToken";

beforeEach(() => {
  clearAccessToken();
});

describe("authToken", () => {
  it("starts empty", () => {
    expect(getAccessToken()).toBeNull();
  });

  it("returns a stored token until it is cleared", () => {
    setAccessToken("abc", new Date(Date.now() + 60_000));
    expect(getAccessToken()).toBe("abc");

    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });

  it("treats an expired token as absent", () => {
    setAccessToken("abc", new Date(Date.now() - 1_000));
    expect(getAccessToken()).toBeNull();
  });

  it("treats a token about to expire as absent", () => {
    setAccessToken("abc", new Date(Date.now() + 5_000));
    expect(getAccessToken()).toBeNull();
  });
});
