import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_BASE_URL, authFetch, parseOrThrow, throwIfError } from "@/lib/apiClient";
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

const PICTURE_REQUESTS_QUERY_KEY = "picture-requests";

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
  const res = await authFetch(`${API_BASE_URL}/requests/?${params}`);
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
    queryKey: [PICTURE_REQUESTS_QUERY_KEY, count, offset],
    queryFn: () => fetchPictureRequests(count, offset),
  });
};

/**
 * @brief Delete a picture request through the URL the backend advertised for it.
 * @param url the request's `operations.delete.url`.
 * @throws ApiError when the backend refuses the delete (e.g. the window has closed).
 */
async function deletePictureRequest(url: string): Promise<void> {
  await throwIfError(await authFetch(url, { method: "DELETE" }));
}

/**
 * @brief Mutation hook deleting a picture request and refreshing the request list.
 *
 * Takes the `operations.delete.url` from a {@link PictureRequest} rather than an
 * id, so whether a request is deletable is decided only by the backend. The list
 * is refetched even when the delete fails, so stale operations disappear.
 *
 * @return useMutation result object; call `mutate(request.operations.delete.url)`.
 */
export const useDeletePictureRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deletePictureRequest,
    onSettled: () => queryClient.invalidateQueries({ queryKey: [PICTURE_REQUESTS_QUERY_KEY] }),
  });
};
