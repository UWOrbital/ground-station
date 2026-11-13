import LatestImageCard from "@/components/dashboard/LatestImageCard";
import RecentTelemetryCard from "@/components/dashboard/RecentTelemetryCard";

/**
 * @brief Dashboard component displaying the satellite's latest image
 * @return tsx element of Dashboard component
 */
function Dashboard() {
  return (
    <div className="flex flex-col gap-6 items-center justify-center min-h-screen px-4 pt-32">
      <LatestImageCard />
      <RecentTelemetryCard />
    </div>
  );
}

export default Dashboard;
