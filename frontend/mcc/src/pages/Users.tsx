import { useState, useMemo } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { Search, ArrowUpDown, Shield, ShieldAlert, User as UserIcon } from "lucide-react";
import { toast } from "react-toastify";

// Define the User type
type Role = "Admin" | "Operator" | "Observer";

type User = {
  id: string;
  name: string;
  email: string;
  role: Role;
  joinedAt: string;
  status: "Active" | "Inactive";
};

// Initial Mock Data
const INITIAL_USERS: User[] = [
  { id: "1", name: "Alice Smith", email: "alice@example.com", role: "Admin", joinedAt: "2025-01-15", status: "Active" },
  { id: "2", name: "Bob Jones", email: "bob@example.com", role: "Operator", joinedAt: "2025-02-20", status: "Active" },
  { id: "3", name: "Charlie Brown", email: "charlie@example.com", role: "Observer", joinedAt: "2025-03-10", status: "Inactive" },
  { id: "4", name: "Diana Prince", email: "diana@example.com", role: "Observer", joinedAt: "2025-04-05", status: "Active" },
  { id: "5", name: "Evan Wright", email: "evan@example.com", role: "Operator", joinedAt: "2025-05-12", status: "Active" },
  { id: "6", name: "Fiona Gallagher", email: "fiona@example.com", role: "Observer", joinedAt: "2025-06-01", status: "Active" },
];

const columnHelper = createColumnHelper<User>();

function Users() {
  const [users, setUsers] = useState<User[]>(INITIAL_USERS);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [searchQuery, setSearchQuery] = useState("");

  // Handler to promote to Operator
  const handlePromoteToOperator = (userId: string) => {
    setUsers((prevUsers) =>
      prevUsers.map((user) =>
        user.id === userId ? { ...user, role: "Operator" } : user
      )
    );
    toast.success("User promoted to Operator successfully!");
  };

  // Define columns
  const columns = useMemo(() => [
    columnHelper.accessor("name", {
      header: ({ column }) => {
        return (
          <button
            className="flex items-center gap-1 hover:text-foreground transition-colors"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Name
            <ArrowUpDown className="h-4 w-4" />
          </button>
        );
      },
      cell: (info) => (
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-accent flex items-center justify-center text-accent-foreground font-semibold">
            {info.getValue().charAt(0)}
          </div>
          <span className="font-medium">{info.getValue()}</span>
        </div>
      ),
    }),
    columnHelper.accessor("email", {
      header: ({ column }) => {
        return (
          <button
            className="flex items-center gap-1 hover:text-foreground transition-colors"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Email
            <ArrowUpDown className="h-4 w-4" />
          </button>
        );
      },
      cell: (info) => <span className="text-muted-foreground">{info.getValue()}</span>,
    }),
    columnHelper.accessor("role", {
      header: ({ column }) => {
        return (
          <button
            className="flex items-center gap-1 hover:text-foreground transition-colors"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Role
            <ArrowUpDown className="h-4 w-4" />
          </button>
        );
      },
      cell: (info) => {
        const role = info.getValue();
        let Icon = UserIcon;
        let colorClass = "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300";
        
        if (role === "Admin") {
          Icon = ShieldAlert;
          colorClass = "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300";
        } else if (role === "Operator") {
          Icon = Shield;
          colorClass = "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300";
        }

        return (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${colorClass}`}>
            <Icon className="w-3.5 h-3.5" />
            {role}
          </span>
        );
      },
    }),
    columnHelper.accessor("status", {
      header: "Status",
      cell: (info) => {
        const isSelected = info.getValue() === "Active";
        return (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${isSelected ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
            {info.getValue()}
          </span>
        );
      },
    }),
    columnHelper.display({
      id: "actions",
      header: "Actions",
      cell: (info) => {
        const user = info.row.original;
        // Mock permission logic: assume only Observer can be escalated to Operator
        if (user.role === "Observer") {
          return (
            <button
              onClick={() => handlePromoteToOperator(user.id)}
              className="text-xs border border-primary text-primary hover:bg-primary hover:text-primary-foreground px-3 py-1.5 rounded transition-colors"
            >
              Escalate to Operator
            </button>
          );
        }
        return <span className="text-muted-foreground text-xs italic">No actions</span>;
      },
    }),
  ], []);

  const table = useReactTable({
    data: users,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="max-w-7xl mx-auto px-8 py-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground mt-1">Manage user roles and statuses.</p>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search users... (mock)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-4 py-2 border border-input rounded-md bg-background w-full md:w-64 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all transition-colors"
          />
        </div>
      </div>

      <div className="rounded-lg border border-border overflow-hidden bg-card text-card-foreground shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 border-b border-border">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th key={header.id} className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.length ? (
                table.getRowModel().rows.map((row) => (
                  <tr key={row.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="p-4 align-middle">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={columns.length} className="h-24 text-center">
                    No results found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-end space-x-2 py-4 px-4 border-t border-border bg-muted/20">
          <div className="text-xs text-muted-foreground">
            {table.getFilteredRowModel().rows.length} user(s) total
          </div>
        </div>
      </div>
    </div>
  );
}

export default Users;
