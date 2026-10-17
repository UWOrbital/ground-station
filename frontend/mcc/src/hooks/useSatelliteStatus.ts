import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL, parseOrThrow } from "@/lib/apiClient";
import type { SatelliteStatus } from "@/components/SatelliteStatusIndicator";


/**
 * One telemetry reading in the satellite status snapshot.
 */
export interface StatusTelemetry {
  label: string;
  value: string;
  unit: string | null;
}

/**
 * Satellite status snapshot returned by the backend.
 */
export interface SatelliteStatusResponse {
  status: SatelliteStatus;
  last_contact: string;
  session_duration: string;
  telemetry_data: StatusTelemetry[];
}

/**
 * @brief Fetch the current satellite status from the MCC backend.
 * @return the satellite status snapshot.
 */
async function fetchSatelliteStatus(): Promise<SatelliteStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/status/status`, {
    credentials: "include",
  });
  return parseOrThrow<SatelliteStatusResponse>(res);
}

/**
 * @brief React Query hook that fetches the satellite status.
 *
 * Polls every 30 seconds so the indicator follows session changes.
 *
 * @param enabled whether to fetch; pass false when logged out.
 * @return useQuery result object with the status snapshot.
 */
export const useSatelliteStatus = (enabled: boolean) => {
  return useQuery({
    queryKey: ["satellite-status"],
    queryFn: fetchSatelliteStatus,
    refetchInterval: 30_000,
    enabled,
  });
};
