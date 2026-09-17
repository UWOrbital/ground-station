import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { isSessionLockedOut, SESSION_LOCKOUT_SECONDS } from "@/utils/lockout";

describe("isSessionLockedOut", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("is open before the lockout window", () => {
    expect(isSessionLockedOut("2026-01-01T12:00:11Z")).toBe(false);
  });

  it("locks exactly at the window boundary", () => {
    expect(isSessionLockedOut(new Date(Date.now() + SESSION_LOCKOUT_SECONDS * 1000))).toBe(true);
  });

  it("stays locked once the session has started", () => {
    expect(isSessionLockedOut("2026-01-01T11:00:00Z")).toBe(true);
  });
});
