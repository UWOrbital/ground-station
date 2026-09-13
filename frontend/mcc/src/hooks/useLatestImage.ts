import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/apiClient";

/**
 * A satellite image record returned by the backend.
 */
export interface ImageResponse {
  id: string;
  data: string;
}

/**
 * @brief Fetch the latest satellite image from the MCC backend.
 * @return the latest image record.
 */
async function fetchLatestImage(): Promise<ImageResponse> {
  const res = await fetch(`${API_BASE_URL}/images/latest`, {
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  const json: ImageResponse | { message: string } = await res.json();
  if ("message" in json) {
    throw new Error(json.message);
  }
  return json;
}

/**
 * @brief React Query hook that fetches the latest satellite image.
 *
 * Polls every 30 seconds to pick up new downlinks during a pass.
 *
 * @return useQuery result object with image data.
 */
export const useLatestImage = () => {
  return useQuery({
    queryKey: ["latest-image"],
    queryFn: fetchLatestImage,
    refetchInterval: 30_000,
  });
};
