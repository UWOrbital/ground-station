/**
 * API functions for satellite images.
 */

export interface ImageData {
  id: string;
  data: string;
}

export interface ImageResponse {
  id: string;
  data: string;
}

/**
 * @brief React hook that exposes API methods for images.
 * @return object with getLatestImage function
 */
export const useImagesApi = () => {
  const getLatestImage = async (): Promise<ImageResponse> => {
    const res = await fetch("/api/v1/mcc/images/latest");
    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }
    const json: ImageResponse | { message: string } = await res.json();
    if ("message" in json) {
      throw new Error(json.message);
    }
    return json;
  };

  return { getLatestImage };
};
