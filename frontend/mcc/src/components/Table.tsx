import {
  useTable,
  tableFeatures,
  rowSortingFeature,
  columnFilteringFeature,
  columnVisibilityFeature,
  globalFilteringFeature,
  createSortedRowModel,
  createFilteredRowModel,
  flexRender,
} from "@tanstack/react-table";
import type { ColumnDef, RowData, SortingState } from "@tanstack/react-table";
import { useState } from "react";

// Register features that Table uses
export const features = tableFeatures({
  rowSortingFeature,
  columnFilteringFeature,
  globalFilteringFeature,
  columnVisibilityFeature,
  sortedRowModel: createSortedRowModel(),
  filteredRowModel: createFilteredRowModel(),
});

interface TableProps<T extends RowData> {
  data: T[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  columns: ColumnDef<typeof features, T, any>[];
  onRowClick?: (row: T) => void;
  showFilters?: boolean;
  containerClassName?: string;
}

/**
 * @brief Reusable Table component with filtering and sorting capabilities
 * @param data - Array of data objects to display
 * @param columns - Column definitions using TanStack Table's ColumnDef
 * @param onRowClick - Optional callback when a row is clicked
 * @param showFilters - Whether to show filter inputs (default: true)
 * @param containerClassName - Optional custom className for the container
 * @return tsx element of Table component
 */
function Table<T extends RowData>({
  data,
  columns,
  onRowClick,
  showFilters = true,
  containerClassName = "w-full max-w-5xl",
}: TableProps<T>) {
  const [globalFilter, setGlobalFilter] = useState("");
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useTable({
    features,
    data,
    columns,
    state: {
      globalFilter,
      sorting,
    },
    onGlobalFilterChange: setGlobalFilter,
    onSortingChange: setSorting,
  });

  return (
    <div className={containerClassName}>
      {/* Filter Section */}
      {showFilters && (
        <div className="flex justify-between mb-6 gap-4">
          <input
            type="text"
            placeholder="Search..."
            value={globalFilter ?? ""}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="flex-1 bg-input text-foreground px-4 py-2 rounded-lg border border-border focus:outline-none focus:border-ring"
          />
        </div>
      )}

      {/* Table */}
      <div className="bg-card backdrop-blur-sm rounded-lg overflow-hidden border border-border">
        <table className="w-full text-foreground">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-border">
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort();
                  const isSorted = header.column.getIsSorted();
                  return (
                    <th
                      key={header.id}
                      className={`text-left px-6 py-4 font-normal text-muted-foreground ${
                        canSort ? "cursor-pointer select-none hover:text-foreground" : ""
                      }`}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center gap-2">
                        {header.isPlaceholder
                          ? null
                          : flexRender(header.column.columnDef.header, header.getContext())}
                        <span className="w-4 inline-block text-xs">
                          {{
                            asc: "▲",
                            desc: "▼",
                          }[isSorted as string] ?? ""}
                        </span>
                      </div>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className={`border-b border-border hover:bg-accent transition-colors ${
                  onRowClick ? "cursor-pointer" : ""
                }`}
                onClick={() => onRowClick?.(row.original)}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-6 py-4 text-foreground">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Table;
