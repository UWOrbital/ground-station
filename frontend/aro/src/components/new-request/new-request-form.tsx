import "./new-request-form.css";
import InputForm from "./input-form";
import MapView from "./map-view";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { useCreatePictureRequest } from "@/hooks/usePictureRequests";
import { ApiError } from "@/lib/apiClient";
import toastService from "@/services/Toast.service";
import { roundCoord, ValidateCoords } from "@/utils/validate_coords";

export async function getUserLocation(): Promise<{ latitude: number; longitude: number }> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation not supported"));
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      (error) => {
        console.error("Geolocation error:", error);
        reject(error);
      },
    );
  });
}

const NewRequestForm = () => {
  const queryClient = useQueryClient();
  const createRequest = useCreatePictureRequest();
  const {
    data: location,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["coords"],
    queryFn: getUserLocation,
    staleTime: Infinity,
    retry: false,
  });

  const latitude = location?.latitude ?? null;
  const longitude = location?.longitude ?? null;

  /**
   * @brief Handle both form buttons: "Validate" saves the coordinates locally,
   * "Submit" also creates a picture request on the backend.
   * @param e the form submit event; its submitter tells the two buttons apart.
   */
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const formData = new FormData(e.currentTarget);
    const parsedLatitude = parseFloat(formData.get("latitude") as string);
    const parsedLongitude = parseFloat(formData.get("longitude") as string);

    const nativeEvent = e.nativeEvent as SubmitEvent;
    const submitter = nativeEvent.submitter as HTMLButtonElement | null;
    const action = submitter?.value;

    if (isNaN(parsedLatitude) || isNaN(parsedLongitude)) return;

    // The backend stores 3 decimal places and rejects anything more precise.
    const newLatitude = roundCoord(parsedLatitude);
    const newLongitude = roundCoord(parsedLongitude);

    if (!ValidateCoords(newLatitude, newLongitude)) {
      toastService.error("Please enter valid coordinates!");
      return;
    }

    queryClient.setQueryData(["coords"], {
      latitude: newLatitude,
      longitude: newLongitude,
    });

    if (action === "Validate") {
      toastService.success("Coordinates validated and saved!");
    } else if (action === "Submit") {
      createRequest.mutate(
        { latitude: newLatitude, longitude: newLongitude },
        {
          onSuccess: () => {
            toastService.success(`Request submitted at (${newLatitude}, ${newLongitude})`);
          },
          onError: (err) => {
            const signedOut = err instanceof ApiError && err.status === 401;
            toastService.error(signedOut ? "Please log in to submit a request." : err.message);
          },
        },
      );
    }
  };

  if (isLoading) {
    return <div className="p-4 text-gray-600">Fetching your location...</div>;
  }

  if (isError) {
    return <div className="p-4 text-red-600">Failed to get your location.</div>;
  }

  return (
    <div className="form-container flex mt-25">
      <div className="w-1/4 max-h-500 overflow-auto">
        <InputForm handleSubmit={handleSubmit} isSubmitting={createRequest.isPending} />
      </div>
      {latitude !== null && longitude !== null && (
        <div className="flex-1">
          <MapView />
        </div>
      )}
    </div>
  );
};

export default NewRequestForm;
