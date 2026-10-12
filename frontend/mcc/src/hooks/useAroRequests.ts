import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL, jsonHeaders, parseOrThrow } from "@/lib/apiClient";
import type { ARORequest } from "@/utils/types";

interface ARORequestResponse {
  data: ARORequest[];
}

async function fetchAroRequests(count: number, offset: number): Promise<ARORequest[]> {
  const params = new URLSearchParams({
    count: String(count),
    offset: String(offset),
  });
  const res = await fetch(`${API_BASE_URL}/requests/?${params}`, {
    credentials: "include",
    headers: jsonHeaders(),
  });
  const json = await parseOrThrow<ARORequestResponse>(res);
  return json.data;
}

const REQUESTS_POLL_INTERVAL_MS = 10_000;

export const useAroRequests = (count: number = 100, offset: number = 0) => {
  return useQuery({
    queryKey: ["requests", count, offset],
    queryFn: () => fetchAroRequests(count, offset),
    refetchInterval: REQUESTS_POLL_INTERVAL_MS,
  });
};
