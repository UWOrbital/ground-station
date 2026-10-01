import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import type { AuthState } from "@/contexts/AuthContext";

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

/**
 * @brief Build a minimal fake fetch Response carrying a JSON body.
 * @param status HTTP status code; 2xx statuses are reported as ok.
 * @param body value returned from `json()`.
 * @return an object that satisfies the parts of Response the app reads.
 */
export function jsonResponse(status: number, body: unknown = {}): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

/**
 * @brief Build a successful `/auth/login` or `/auth/rotate_tokens` response body.
 * @param token the access token value to hand out.
 * @return an AccessTokenResponse-shaped body expiring in ten minutes.
 */
export function tokenBody(token: string = "access-token") {
  return {
    access_token: token,
    token_type: "bearer",
    expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
  };
}

/**
 * @brief Mock global fetch, answering each call by the first route whose path the URL contains.
 * @param routes map of URL substring to a response, or a function producing one per call.
 * @return the fetch spy, for asserting on calls.
 */
export function mockFetchByPath(routes: Record<string, Response | (() => Response)>) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    const path = Object.keys(routes).find((key) => url.includes(key));
    if (!path) throw new Error(`Unmocked fetch: ${url}`);
    const route = routes[path];
    return typeof route === "function" ? route() : route;
  });
}

/**
 * @brief List the URLs a fetch spy was called with, in order.
 * @param fetchSpy the spy returned by {@link mockFetchByPath} or vi.spyOn.
 * @return the requested URLs as strings.
 */
export function calledUrls(fetchSpy: { mock: { calls: unknown[][] } }): string[] {
  return fetchSpy.mock.calls.map((call) => String(call[0]));
}

/**
 * @brief Build a full AuthState for tests that mock `useAuth`.
 *
 * Defaults to a settled, signed-out state with no-op actions.
 *
 * @param overrides the fields to change from the defaults.
 * @return a complete AuthState.
 */
export function fakeAuthState(overrides: Partial<AuthState> = {}): AuthState {
  return {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    isUnavailable: false,
    recheck: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  };
}
