import { describe, expect, it, vi } from "vitest";
import { getStartingLocation, getUserLocation, UW_DEFAULT_LOCATION } from "./new-request-form";

function geolocationThatReturns(latitude: number, longitude: number): Geolocation {
  return {
    getCurrentPosition: (success) =>
      success({ coords: { latitude, longitude } } as GeolocationPosition),
  } as Geolocation;
}

function geolocationThatFails(): Geolocation {
  return {
    getCurrentPosition: (_success, error) =>
      error?.({
        code: 1,
        message: "Permission denied",
      } as GeolocationPositionError),
  } as Geolocation;
}

describe("getUserLocation", () => {
  it("returns coordinates supplied by browser geolocation", async () => {
    await expect(getUserLocation(geolocationThatReturns(43.5, -80.5))).resolves.toEqual({
      latitude: 43.5,
      longitude: -80.5,
    });
  });

  it("rejects when browser geolocation is unavailable", async () => {
    await expect(getUserLocation(undefined)).rejects.toThrow("Geolocation not supported");
  });
});

describe("getStartingLocation", () => {
  it("uses browser coordinates when permission is granted", async () => {
    await expect(getStartingLocation(geolocationThatReturns(43.5, -80.5))).resolves.toEqual({
      latitude: 43.5,
      longitude: -80.5,
    });
  });

  it("uses the Waterloo default when geolocation fails", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    await expect(getStartingLocation(geolocationThatFails())).resolves.toEqual({
      ...UW_DEFAULT_LOCATION,
      usedDefault: true,
    });
  });
});
