import { useState } from "react";

export type SatelliteStatus = "online" | "idle" | "offline" | "error";

export interface TelemetryData {
  label: string;
  value: string;
  unit?: string;
}

interface StatusConfig {
  label: string;
  accentColor: string;
  textColor: string;
}

//TODO: Should have more states such as Pending , Scheduled , Completed instead of just idle for all of them
const statusConfig: Record<SatelliteStatus, StatusConfig> = {
  online: {
    label: "ONLINE",
    accentColor: "bg-green-500",
    textColor: "text-green-400",
  },
  idle: {
    label: "IDLE",
    accentColor: "bg-yellow-500",
    textColor: "text-yellow-400",
  },
  offline: {
    label: "OFFLINE",
    accentColor: "bg-red-500",
    textColor: "text-red-400",
  },
  error: {
    label: "ERROR",
    accentColor: "bg-red-600",
    textColor: "text-red-500",
  },
};

interface SatelliteStatusIndicatorProps {
  status?: SatelliteStatus;
  lastContact?: string;
  telemetryData?: TelemetryData[];
  sessionDuration?: string;
}

function SatelliteStatusModal({
  isOpen,
  onClose,
  status,
  lastContact,
  telemetryData,
  sessionDuration,
}: {
  isOpen: boolean;
  onClose: () => void;
  status: SatelliteStatus;
  lastContact?: string;
  telemetryData?: TelemetryData[];
  sessionDuration?: string;
}) {
  if (!isOpen) return null;

  const config = statusConfig[status];

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="fixed top-20 right-8 z-50 w-96 rounded-lg border border-border bg-background shadow-lg animate-in fade-in slide-in-from-top-2">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="relative flex h-3 w-3">
              <span
                className={`absolute inline-flex h-full w-full rounded-full ${config.accentColor} ${
                  status === "online" ? "animate-pulse" : ""
                }`}
              ></span>
              {status === "online" && (
                <span
                  className={`absolute inline-flex h-full w-full rounded-full ${config.accentColor.replace(
                    "500",
                    "400",
                  )} animate-ping`}
                ></span>
              )}
            </div>
            <h3 className="font-semibold text-card-foreground">Satellite Status</h3>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            aria-label="Close"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 6l-12 12" />
              <path d="M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-4">
          {/* Status Section */}
          <div>
            <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Status</p>
            <p className={`text-lg font-semibold ${config.textColor}`}>{config.label}</p>
          </div>

          {/* Last Contact */}
          {lastContact && (
            <div>
              <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                Last Contact
              </p>
              <p className="text-sm text-foreground">{lastContact}</p>
            </div>
          )}

          {/* Session Duration */}
          {sessionDuration && (
            <div>
              <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                Session Duration
              </p>
              <p className="text-sm text-foreground">{sessionDuration}</p>
            </div>
          )}

          {/* Telemetry Data */}
          <div className="border-t border-border pt-4">
            <p className="text-xs uppercase tracking-wider text-muted-foreground mb-3">Telemetry</p>
            {telemetryData && telemetryData.length > 0 ? (
              <div className="space-y-2">
                {telemetryData.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">{item.label}</span>
                    <span className="text-sm font-medium text-foreground">
                      {item.value}
                      {item.unit && <span className="text-xs ml-1">{item.unit}</span>}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground italic">No telemetry data available</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

/**
 * @brief Mission-critical satellite status indicator for the navbar
 * Displays real-time satellite communication status with visual indicators
 * Click to view detailed telemetry data in a modal
 * @return tsx element of SatelliteStatusIndicator component
 */
function SatelliteStatusIndicator({
  status = "offline",
  lastContact = "Never",
  telemetryData,
  sessionDuration = "--",
}: SatelliteStatusIndicatorProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const config = statusConfig[status];

  return (
    <>
      {/* Compact Status Indicator Button */}
      <button
        onClick={() => setIsModalOpen(true)}
        className="flex items-center gap-2 px-3 py-2 rounded-md border border-foreground/20 transition-all duration-200 hover:bg-accent cursor-pointer"
        title={`Satellite Status: ${config.label}. Click for details.`}
        aria-label={`Satellite status: ${config.label}`}
      >
        {/* Animated Status Dot */}
        <div className="relative flex h-2 w-2">
          <span
            className={`absolute inline-flex h-full w-full rounded-full ${config.accentColor} ${
              status === "online" ? "animate-pulse" : ""
            }`}
          ></span>
          {status === "online" && (
            <span
              className={`absolute inline-flex h-full w-full rounded-full ${config.accentColor.replace(
                "500",
                "400",
              )} animate-ping`}
            ></span>
          )}
        </div>

        {/* Status Label */}
        <span className={`text-xs font-semibold tracking-wider ${config.textColor}`}>
          {config.label}
        </span>
      </button>

      {/* Detailed Modal */}
      <SatelliteStatusModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        status={status}
        lastContact={lastContact}
        telemetryData={telemetryData}
        sessionDuration={sessionDuration}
      />
    </>
  );
}

export default SatelliteStatusIndicator;
