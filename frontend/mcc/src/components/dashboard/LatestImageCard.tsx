import { useLatestImage } from "@/hooks/useLatestImage";

/**
 * @brief Displays the latest satellite image on the MCC dashboard
 * @return tsx element of LatestImageCard component
 */

function LatestImageCard(){
    const { data: image, isLoading, isError, error } = useLatestImage();

    return (
        <div className="bg-card border border-border rounded-lg p-4">
            <h2>Latest Image</h2>
            {isLoading && <p className="text-lg text-muted-foreground">Loading image...</p>}
            {isError && <p className="text-lg text-destructive">{(error as Error)?.message}</p>}
            {image && 
                <img
                    src={`data:image/jpeg;base64,${image.data}`}
                    alt="Latest satellite downlink"
                    className="max-w-full max-h-80 rounded-lg border border-border shadow-lg"
                />
            }
        </div>
    )
}

export default LatestImageCard;