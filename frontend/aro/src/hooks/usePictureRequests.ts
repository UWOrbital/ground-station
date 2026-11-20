import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_BASE_URL, authFetch, parseOrThrow } from "@/lib/apiClient";
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
 * in `@/types`. Coordinates are backend `Decimal`s, which serialize to JSON strings.
 */
export interface PictureRequest {
  id: string;
  aro_id: string | null;
  latitude: string;
  longitude: string;
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

interface PictureRequestResponse {
  data: PictureRequest;
}

/**
 * Coordinates submitted to create a new picture request, in decimal degrees.
 */
interface CreatePictureRequestPayload {
  latitude: number;
  longitude: number;
}

/** Query key prefix shared by every picture-request list query. */
const PICTURE_REQUESTS_QUERY_KEY = ["picture-requests"] as const;

/**
 * @brief Fetch a page of the current ARO user's most recent picture requests.
 * @param limit maximum number of most recent requests to return.
 * @param offset number of most recent requests to skip, for paging.
 * @return list of the user's picture requests.
 */
async function fetchPictureRequests(limit: number, offset: number): Promise<PictureRequest[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const res = await authFetch(`${API_BASE_URL}/requests/?${params}`);
  const json = await parseOrThrow<PictureRequestsResponse>(res);
  return json.data;
}

/**
 * @brief React Query hook fetching the current ARO user's picture requests.
 * @param limit maximum number of most recent requests to return (defaults to 100).
 * @param offset number of most recent requests to skip, for paging (defaults to 0).
 * @return useQuery result object with the list of picture requests.
 */
export const usePictureRequests = (limit: number = 100, offset: number = 0) => {
  return useQuery({
    queryKey: [...PICTURE_REQUESTS_QUERY_KEY, limit, offset],
    queryFn: () => fetchPictureRequests(limit, offset),
  });
};

/**
 * @brief Create a picture request for the current ARO user.
 *
 * The backend accepts at most 3 decimal places per coordinate, so callers
 * must round first (see `roundCoord` in `@/utils/validate_coords`).
 *
 * @param payload the coordinates to photograph.
 * @return the created picture request.
 * @throws ApiError when the backend rejects the request.
 */
async function createPictureRequest(payload: CreatePictureRequestPayload): Promise<PictureRequest> {
  const res = await authFetch(`${API_BASE_URL}/requests/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const json = await parseOrThrow<PictureRequestResponse>(res);
  return json.data;
}

/**
 * @brief React Query mutation hook creating a picture request.
 *
 * On success it invalidates every picture-request list so they refetch.
 *
 * @return useMutation result object; call mutate/mutateAsync with the coordinates.
 */
export const useCreatePictureRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createPictureRequest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PICTURE_REQUESTS_QUERY_KEY }),
  });
};
