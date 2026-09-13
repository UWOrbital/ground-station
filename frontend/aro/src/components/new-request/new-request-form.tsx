import "./new-request-form.css";
import InputForm from "./input-form";
import MapView from "./map-view";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";

// define an interface for DA coordinates once more, to make readable code
export interface Coordinates {
  latitude: number;
  longitude: number;
  usedDefault?: boolean;
}

// Keep the request form usable when browser geolocation is unavailable for coords to our BEAUTIFUL columbia lake!!.
export const UW_DEFAULT_LOCATION: Coordinates = {
  latitude: 43.4723,
  longitude: -80.5449,
};

export function isInvalidCoordinate(lat: number, lng: number): boolean {
  if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
    return true;
  } else {
    return false;
  }
}
// Request the device's current coordinates through the browser Geolocation API and if not, then fallback to DEFAULT!!
export async function getUserLocation(
  geolocation: Geolocation | undefined = navigator.geolocation,
): Promise<Coordinates> {
  return new Promise((resolve, reject) => {
    if (!geolocation) {
      reject(new Error("Geolocation not supported"));
      return;
    }

    geolocation.getCurrentPosition(
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
      {
        enableHighAccuracy: false,
        timeout: 10_000,
        maximumAge: 300_000,
      },
    );
  });
}

// Try to resolve the map's starting point issue and fall back to the one and only COLUMBIA LAKE if geolocation fails!!
export async function getStartingLocation(
  geolocation: Geolocation | undefined = navigator.geolocation,
): Promise<Coordinates> {
  try {
    return await getUserLocation(geolocation);
  } catch {
    return {
      ...UW_DEFAULT_LOCATION,
      usedDefault: true,
    };
  }
}

const NewRequestForm = (): React.JSX.Element => {
  useEffect(() => {
    alert(
      "Welcome to the new request form! Enter your coordinates on the left or select them on the map by holding Shift and clicking your desired location.",
    );
  }, []);

  const queryClient = useQueryClient();
  const { data: location, isLoading } = useQuery({
    queryKey: ["coords"],
    // TODO(#69): Prefer saved user coordinates once ARO user settings expose them.
    queryFn: () => getStartingLocation(),
    staleTime: 300_000,
    refetchOnMount: "always",
    retry: false,
  });

  const latitude = location?.latitude ?? null;
  const longitude = location?.longitude ?? null;

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();

    const formData = new FormData(e.currentTarget);
    const newLatitude = parseFloat(formData.get("latitude") as string);
    const newLongitude = parseFloat(formData.get("longitude") as string);

    const nativeEvent = e.nativeEvent as SubmitEvent;
    const submitter = nativeEvent.submitter as HTMLButtonElement | null;
    const action = submitter?.value;

    if (isNaN(newLatitude) || isNaN(newLongitude)) return;

    if (isInvalidCoordinate(newLatitude, newLongitude)) {
      alert("Please enter valid coordinates!");
      return;
    }

    queryClient.setQueryData<Coordinates>(["coords"], {
      latitude: newLatitude,
      longitude: newLongitude,
      usedDefault: false,
    });

    if (action === "Validate") {
      alert("Coordinates validated and saved!");
    } else if (action === "Submit") {
      alert(`Request submitted at (${newLatitude}, ${newLongitude})`);
    }
  };

  if (isLoading) {
    return <div className="p-4 text-gray-600">Fetching your location...</div>;
  }

  return (
    <>
      {location?.usedDefault && (
        <p role="status" className="absolute top-24 text-sm text-white">
          Your location could not be determined. Showing the default map location.
        </p>
      )}

      <div className="form-container flex mt-25">
        <div className="w-1/4 max-h-500 overflow-auto">
          <InputForm handleSubmit={handleSubmit} />
        </div>
        {latitude !== null && longitude !== null && (
          <div className="flex-1">
            <MapView />
          </div>
        )}
      </div>
    </>
  );
};

export default NewRequestForm;
