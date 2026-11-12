import LatestImageCard from "@/components/dashboard/LatestImageCard";

/**
 * @brief Dashboard component displaying the satellite's latest image
 * @return tsx element of Dashboard component
 */
function Dashboard() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 pt-32">
      <LatestImageCard/>
    </div>
  );
}

export default Dashboard;
