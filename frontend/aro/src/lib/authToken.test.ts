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
    setAccessToken("abc");
    expect(getAccessToken()).toBe("abc");

    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });
});
