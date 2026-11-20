import { describe, expect, it } from "vitest";
import { roundCoord, ValidateCoords } from "./validate_coords";

describe("roundCoord", () => {
  it("rounds to 3 decimal places", () => {
    expect(roundCoord(43.47234)).toBe(43.472);
    expect(roundCoord(-80.54489)).toBe(-80.545);
    expect(roundCoord(12.3456)).toBe(12.346);
  });

  it("leaves values that are already precise enough unchanged", () => {
    expect(roundCoord(43.472)).toBe(43.472);
    expect(roundCoord(90)).toBe(90);
    expect(roundCoord(-180)).toBe(-180);
  });

  it("serializes to at most 3 decimal places", () => {
    const decimals = (n: number) => (String(n).split(".")[1] ?? "").length;
    for (const value of [0.1 + 0.2, 1 / 3, 179.99949, -89.123456789]) {
      expect(decimals(roundCoord(value))).toBeLessThanOrEqual(3);
    }
  });

  it("can round a value just past a bound onto the bound or beyond it", () => {
    expect(roundCoord(90.0004)).toBe(90);
    expect(ValidateCoords(roundCoord(90.0004), 0)).toBe(true);
    expect(roundCoord(90.0006)).toBe(90.001);
    expect(ValidateCoords(roundCoord(90.0006), 0)).toBe(false);
  });
});

describe("ValidateCoords", () => {
  it("accepts the inclusive bounds", () => {
    expect(ValidateCoords(90, 180)).toBe(true);
    expect(ValidateCoords(-90, -180)).toBe(true);
  });

  it("rejects values outside the bounds", () => {
    expect(ValidateCoords(90.001, 0)).toBe(false);
    expect(ValidateCoords(-90.001, 0)).toBe(false);
    expect(ValidateCoords(0, 180.001)).toBe(false);
    expect(ValidateCoords(0, -180.001)).toBe(false);
  });
});
