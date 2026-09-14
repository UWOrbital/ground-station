import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/apiClient";

/** A subrow (packet-level detail) of a telemetry entry. */
export interface TelemetrySubrow {
  packet: string;
  session: string;
  obc_state: string;
}

/** Backend shape of a single telemetry entry from GET /api/mcc/telemetry/. */
export interface TelemetryEntry {
  id: string;
  type: string;
  value: string | null;
  timestamp: string;
  subrows: TelemetrySubrow[] | null;
}

/** Backend response wrapper for the telemetry list. */
export interface TelemetryResponse {
  data: TelemetryEntry[];
}

/**
 * @brief Fetch telemetry data from the MCC backend.
 * @return parsed telemetry response payload.
 */
async function fetchTelemetry(): Promise<TelemetryResponse> {
  const response = await fetch(`${API_BASE_URL}/telemetry/`, {
    method: "GET",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch telemetry");
  }

  return response.json();
}

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
  return useQuery({
    queryKey: ["telemetry"],
    queryFn: fetchTelemetry,
    refetchInterval: 10_000,
  });
};
