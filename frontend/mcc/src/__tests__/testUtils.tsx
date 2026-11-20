import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { Session } from "@/utils/types";

/**
 * @brief Build a Session fixture that looks like the API response for a manual session.
 * @param overrides fields to replace.
 * @return a complete Session object.
 */
export function makeSession(overrides: Partial<Session> = {}): Session {
  return {
    id: "00000000-0000-0000-0000-000000000000",
    start_time: "2026-01-01T00:00:00Z",
    end_time: "2026-01-01T00:10:00Z",
    status: "pending",
    source: "manual",
    rise_time: null,
    peak_time: null,
    set_time: null,
    min_elevation_deg: null,
    max_elevation_deg: null,
    rise_azimuth_deg: null,
    set_azimuth_deg: null,
    orbit_element_id: null,
    orphaned_at: null,
    ...overrides,
  };
}

/**
 * @brief Build a React Query provider wrapper for hook tests.
 *
 * Retries are disabled and gcTime is zeroed so failing queries surface their
 * error immediately and state does not leak between tests.
 *
 * @return a wrapper component that provides a fresh QueryClient.
 */
export function createQueryWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  /**
   * @brief Wrapper component supplying the QueryClient context.
   * @param children the subtree under test.
   * @return the children wrapped in a QueryClientProvider.
   */
  return function QueryWrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}
