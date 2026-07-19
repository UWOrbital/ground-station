export const useTelemetryApi = () => {
  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");

    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const getTelemetry = async () => {
    const headers = getAuthHeaders();
    const url = import.meta.env.VITE_BACKEND_URL + "/api/v1/mcc/telemetry/";

    const response = await fetch(url, {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      throw new Error("Failed to fetch telemetry");
    }

    return response.json();
  };

  return { getTelemetry };
};
