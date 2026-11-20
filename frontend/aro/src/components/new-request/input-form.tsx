import React, { type ChangeEvent, useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

interface InputFormProps {
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  /** True while a submitted request is in flight; disables the submit button. */
  isSubmitting: boolean;
}

/**
 * @brief Latitude/longitude form for a new picture request.
 * @param handleSubmit called for both the "Validate" and "Submit" buttons.
 * @param isSubmitting whether a request is currently being submitted.
 * @return tsx element of the input form.
 */
const InputForm: React.FC<InputFormProps> = ({ handleSubmit, isSubmitting }) => {
  const queryClient = useQueryClient();
  const [localLat, setLocalLat] = useState<number | "">("");
  const [localLng, setLocalLng] = useState<number | "">("");

  const { data: location, dataUpdatedAt } = useQuery<
    { latitude: number; longitude: number },
    Error
  >({
    queryKey: ["coords"],
    queryFn: async () => {
      const cached = queryClient.getQueryData<{ latitude: number; longitude: number }>(["coords"]);
      if (!cached) throw new Error("No coordinates yet");
      return cached;
    },
    staleTime: Infinity,
    retry: true,
  });

  // Also re-sync on dataUpdatedAt: when the saved (rounded) coordinates equal the
  // previous ones, React Query keeps the same `location` object, but the inputs
  // may still show the unrounded text the user typed.
  useEffect(() => {
    if (location) {
      setLocalLat(location.latitude);
      setLocalLng(location.longitude);
    }
  }, [location, dataUpdatedAt]);

  const handleLatitudeChange = (event: ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setLocalLat(value === "" ? "" : parseFloat(value));
  };

  const handleLongitudeChange = (event: ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setLocalLng(value === "" ? "" : parseFloat(value));
  };

  return (
    <div className="flex flex-col items-center justify-start min-h-screen bg-white text-lg pt-24">
      <div className="w-full max-w-lg p-8 bg-white rounded-lg">
        <h1 className="text-3xl text-center -mt-11 mb-4">New Request Form</h1>
        <p className="text-base text-gray-600 text-center mb-10">
          Enter coordinates below, or hold Shift and click a location on the map.
        </p>
        <form onSubmit={handleSubmit} className="flex flex-col space-y-6 w-full">
          <div className="flex flex-col w-full">
            <label className="text-base font-medium text-gray-700 mb-2">Latitude</label>
            <input
              type="number"
              name="latitude"
              placeholder="Enter latitude"
              value={localLat}
              onChange={handleLatitudeChange}
              required
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div className="flex flex-col w-full">
            <label className="text-base font-medium text-gray-700 mb-4">Longitude</label>
            <input
              type="number"
              name="longitude"
              placeholder="Enter longitude"
              value={localLng}
              onChange={handleLongitudeChange}
              required
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-lg focus:outline-none focus:ring-2 focus:ring-blue-400 mb-5"
            />
          </div>

          <div className="flex flex-col w-full space-y-4 mt-4">
            <button
              type="submit"
              name="action"
              value="Validate"
              className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 rounded-lg shadow transition text-lg"
            >
              Validate Coordinates
            </button>
            <button
              type="submit"
              name="action"
              value="Submit"
              disabled={isSubmitting}
              className="w-full border border-gray-300 text-black font-medium py-3 rounded-lg shadow-sm hover:bg-gray-50 transition text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Submitting…" : "Submit Request"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InputForm;
