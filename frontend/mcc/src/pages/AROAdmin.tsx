import { createColumnHelper } from "@tanstack/react-table";
import { useAroRequests } from "../hooks/useAroRequests";
import Table from "../components/Table";
import type { ARORequest } from "@/utils/types";


const statusColors: Record<string, string> = {
  pending: "text-yellow-400",
  scheduled: "text-blue-400",
  taken: "text-green-400",
  cancelled: "text-gray-400",
  failed: "text-red-400",
  completed: "text-teal-400",
};

const columnHelper = createColumnHelper<ARORequest>();

const columns = [
  columnHelper.accessor("status", {
    header: "Status",
    cell: (info) => {
      const status = info.getValue();
      return <span className={statusColors[status] || "text-gray-400"}>{status}</span>;
    }
  }),
  columnHelper.accessor("latitude", {
    header: "Latitude",
    cell: (info) => Number(info.getValue()),
  }),
  columnHelper.accessor("longitude", {
    header: "Longitude",
    cell: (info) => Number(info.getValue()),
  }),
  columnHelper.accessor("created_on", {
    header: "Created",
    cell: (info) => new Date(info.getValue()).toLocaleString(),
  }),
  columnHelper.accessor("aro_id", {
    header: "ARO User",
    cell: (info) => info.getValue(),
  }),
];

/**
 * @brief AROAdmin component displaying the ARO admin table
 * @return tsx element of AROAdmin component
 */
function AROAdmin() {
  const { data: request, isLoading, isError, error } = useAroRequests();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-lg text-muted-foreground">Loading requests...</p>
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
    <div className="flex flex-col items-center justify-center min-h-screen px-4 pt-32">
      <Table data={request ?? []} columns={columns} showFilters={true} />
    </div>
  );
}

export default AROAdmin;
