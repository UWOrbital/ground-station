import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useIsMobile } from "@/hooks/use-mobile";

const setWidth = (w: number) =>
  Object.defineProperty(window, "innerWidth", { value: w, configurable: true });

describe("useIsMobile", () => {
  let onChange: (() => void) | undefined;
  const removeEventListener = vi.fn();

  beforeEach(() => {
    vi.spyOn(window, "matchMedia").mockReturnValue({
      addEventListener: (_: string, cb: () => void) => (onChange = cb),
      removeEventListener,
    } as unknown as MediaQueryList);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("is mobile below 768px and follows viewport changes", () => {
    setWidth(500);
    const { result, unmount } = renderHook(() => useIsMobile());
    expect(result.current).toBe(true);

    setWidth(1024);
    act(() => onChange!());
    expect(result.current).toBe(false);

    unmount();
    expect(removeEventListener).toHaveBeenCalledWith("change", onChange);
  });

  it("is not mobile at exactly 768px", () => {
    setWidth(768);
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);
  });
});
