import { useTelemetry } from "@/hooks/useTelemetry";

/**
 * @brief Displays the recent telemetry values on the MCC dashboard
 * @return tsx element of RecentTelemetryCard component
 */
function RecentTelemetryCard(){
    const { data: telemetry, isLoading, isError, error } = useTelemetry();

    return (
        <div className="bg-card border border-border rounded-lg p-4">
            <h2>Recent Telemetry</h2>
            {isLoading && <p className="text-lg text-muted-foreground">Loading...</p>}
            {isError && <p className="text-lg text-destructive">{(error as Error)?.message}</p>}
            {telemetry && telemetry.data.length === 0 && <p className="text-lg text-muted-foreground">No telemetry yet</p>}
            {telemetry && 
                <ul>
                    {/* the backend sends unsorted data so sort it and take the 5 newest entries */}
                    {[...telemetry.data].sort((a, b) => (new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()))
                    .slice(0, 5)
                    .map((entry) =>
                        <li key={entry.id} className="flex gap-4">
                            <span>{entry.type}</span>
                            <span>{entry.value ?? "No value"}</span>
                            <span>{entry.timestamp}</span>
                        </li>
                    )}
                </ul>
            }
        </div>
    )
}

export default RecentTelemetryCard;