import { useQuery } from "@tanstack/react-query";
import { useTelemetryApi } from "../api/telemetry";

/**
 * @brief React Query hook that fetches telemetry data from the backend.
 *
 * Polls on a 10-second interval so the MCC view stays reasonably fresh
 * during a live pass. Consumers receive the standard UseQueryResult shape
 * (data, isLoading, isError, error, refetch, …).
 *
 * @return useQuery result object with telemetry data.
 */
export const useTelemetry = () => {
  const { getTelemetry } = useTelemetryApi();

  return useQuery({
    queryKey: ["telemetry"],
    queryFn: getTelemetry,
    refetchInterval: 10_000,
  });
};
