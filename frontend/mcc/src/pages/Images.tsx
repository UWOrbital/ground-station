import { useLatestImage } from "../hooks/useLatestImage";

/**
 * Displays the most recent satellite image from the backend.
 */
function Images() {
  const { data: image, isLoading, isError, error } = useLatestImage();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-lg text-muted-foreground">Loading image...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-lg text-destructive">{(error as Error)?.message}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <h1 className="text-2xl font-bold mb-6">Latest Satellite Image</h1>
      <img
        src={`data:image/jpeg;base64,${image!.data}`}
        alt="Latest satellite downlink"
        className="max-w-full max-h-[70vh] rounded-lg border border-border shadow-lg"
      />
    </div>
  );
}

export default Images;
