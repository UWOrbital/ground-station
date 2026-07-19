import { useQuery } from "@tanstack/react-query";
import { useImagesApi } from "../api/images";

/**
 * @brief React Query hook that fetches the latest satellite image.
 *
 * Polls every 30 seconds to pick up new downlinks during a pass.
 *
 * @return useQuery result object with image data.
 */
export const useLatestImage = () => {
  const { getLatestImage } = useImagesApi();

  return useQuery({
    queryKey: ["latest-image"],
    queryFn: getLatestImage,
    refetchInterval: 30_000,
  });
};
