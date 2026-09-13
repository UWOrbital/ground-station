import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL, jsonHeaders, parseOrThrow } from "@/lib/apiClient";
import type { MainCommand } from "@/utils/types";

interface MainCommandsResponse {
  data: MainCommand[];
}

/**
 * @brief Fetch the reference table of main commands from the backend.
 * @return list of main commands.
 */
async function fetchMainCommands(): Promise<MainCommand[]> {
  const res = await fetch(`${API_BASE_URL}/main-commands/`, {
    credentials: "include",
    headers: jsonHeaders(),
  });
  const json = await parseOrThrow<MainCommandsResponse>(res);
  return json.data;
}

/**
 * @brief React Query hook fetching the main command reference table.
 * @return useQuery result object with the list of main commands.
 */
export const useMainCommands = () => {
  return useQuery({
    queryKey: ["mainCommands"],
    queryFn: fetchMainCommands,
  });
};
