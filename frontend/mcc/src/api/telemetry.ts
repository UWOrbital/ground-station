import { API_BASE_URL } from "../utils/api/config";

export const useTelemetryApi = () => {
  const getTelemetry = async () => {
    const url = `${API_BASE_URL}/telemetry/`;

    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch telemetry");
    }

    return response.json();
  };

  return { getTelemetry };
};
