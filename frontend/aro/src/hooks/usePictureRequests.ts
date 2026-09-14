import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL, jsonHeaders, parseOrThrow } from "@/lib/apiClient";
import type { AROCommandStatus } from "@/types";

/**
 * An operation link (HATEOAS-style) attached to a picture request or list page.
 */
export interface OperationLink {
  url: string;
  deletable_until?: string;
}

/**
 * A single ARO picture request, matching the backend `PictureRequestItem`.
 *
 * Note: this reflects the live `/api/aro/requests/` payload (UUID ids as
 * strings, nullable timestamps) rather than the stale `ARORequest` interface
 * in `@/types`.
 */
export interface PictureRequest {
  id: string;
  aro_id: string | null;
  latitude: number;
  longitude: number;
  created_on: string;
  request_sent_to_obc_on: string | null;
  pic_taken_on: string | null;
  pic_transmitted_on: string | null;
  delete_deadline: string | null;
  packet_id: string | null;
  status: AROCommandStatus;
  operations: Record<string, OperationLink>;
}

interface PictureRequestsResponse {
  data: PictureRequest[];
  operations: Record<string, OperationLink>;
}

/**
 * @brief Fetch a page of the current ARO user's most recent picture requests.
 * @param count maximum number of most recent requests to return.
 * @param offset number of most recent requests to skip, for paging.
 * @return list of the user's picture requests.
 */
async function fetchPictureRequests(count: number, offset: number): Promise<PictureRequest[]> {
  const params = new URLSearchParams({
    count: String(count),
    offset: String(offset),
  });
  const res = await fetch(`${API_BASE_URL}/requests/?${params}`, {
    credentials: "include",
    headers: jsonHeaders(),
  });
  const json = await parseOrThrow<PictureRequestsResponse>(res);
  return json.data;
}

/**
 * @brief React Query hook fetching the current ARO user's picture requests.
 * @param count maximum number of most recent requests to return (defaults to 100).
 * @param offset number of most recent requests to skip, for paging (defaults to 0).
 * @return useQuery result object with the list of picture requests.
 */
export const usePictureRequests = (count: number = 100, offset: number = 0) => {
  return useQuery({
    queryKey: ["picture-requests", count, offset],
    queryFn: () => fetchPictureRequests(count, offset),
  });
};
