import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

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
