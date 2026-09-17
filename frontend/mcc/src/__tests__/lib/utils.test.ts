import { describe, it, expect } from "vitest";
import { cn } from "@/lib/utils";

describe("cn", () => {
  it("drops falsy classes and lets later conflicting Tailwind utilities win", () => {
    expect(cn("px-2 text-sm", null, undefined, { "font-bold": true, italic: false }, "px-4")).toBe(
      "text-sm font-bold px-4",
    );
  });
});
