import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import { apiGet, apiPost } from "./api";
import type { AROUserKey } from "../types";

const KEYS_QUERY_KEY = ["aro-keys"] as const;
const CURRENT_KEY_QUERY_KEY = ["aro-current-key"] as const;

/**
 * @brief Fetch the current active key
 * @return the current active AROUserKey
 */
async function fetchCurrentKey(): Promise<AROUserKey> {
  return apiGet<AROUserKey>("/keys/current");
}

/**
 * @brief Fetch all keys
 * @return array of all AROUserKey
 */
async function fetchAllKeys(): Promise<AROUserKey[]> {
  return apiGet<AROUserKey[]>("/keys/all");
}

/**
 * @brief Generate a new key
 * @param name optional label for the new key
 * @return the newly created AROUserKey
 */
async function generateKey(name?: string): Promise<AROUserKey> {
  return apiPost<AROUserKey>("/keys/generate", { name: name ?? null });
}

/**
 * @brief Mark a key as synced
 * @param keyId the UUID of the key to mark synced
 * @return the updated AROUserKey
 */
async function syncKey(keyId: string): Promise<AROUserKey> {
  return apiPost<AROUserKey>("/keys/sync", { key_id: keyId });
}

/**
 * @brief React Query hook to fetch the current active key
 * @return query result with the current active key
 */
export function useCurrentKey() {
  return useQuery({
    queryKey: CURRENT_KEY_QUERY_KEY,
    queryFn: fetchCurrentKey,
    refetchInterval: 30_000,
  });
}

/**
 * @brief React Query hook to fetch all keys
 * @return query result with all keys
 */
export function useAllKeys() {
  return useQuery({
    queryKey: KEYS_QUERY_KEY,
    queryFn: fetchAllKeys,
    refetchInterval: 30_000,
  });
}

/**
 * @brief React Query mutation to generate a new key
 * @return mutation object with mutate function
 */
export function useGenerateKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (name?: string) => generateKey(name),
    onSuccess: () => {
      toast.success("New key generated successfully.");
      queryClient.invalidateQueries({ queryKey: KEYS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: CURRENT_KEY_QUERY_KEY });
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate key: ${error.message}`);
    },
  });
}

/**
 * @brief React Query mutation to sync a key
 * @return mutation object with mutate function
 */
export function useSyncKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (keyId: string) => syncKey(keyId),
    onSuccess: () => {
      toast.success("Key marked as synced.");
      queryClient.invalidateQueries({ queryKey: KEYS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: CURRENT_KEY_QUERY_KEY });
    },
    onError: (error: Error) => {
      toast.error(`Failed to sync key: ${error.message}`);
    },
  });
}
