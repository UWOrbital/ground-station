import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import type { MainCommand } from "../utils/types.ts";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

function SelectCommand({
  mainCommands,
  selectedCommandId,
  setSelectedCommandId,
}: {
  mainCommands: MainCommand[];
  selectedCommandId: number | null;
  setSelectedCommandId: (id: number | null) => void;
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className="fixed bottom-10 left-10 z-10 rounded-full w-15 h-15 flex items-center justify-center hover:border-ring hover:ring-ring/50 hover:ring-[2px]"
        >
          <FontAwesomeIcon icon={faPlus} size="xl" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56">
        <DropdownMenuLabel>Commands</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {mainCommands.length === 0 && (
          <div className="px-2 py-1.5 text-sm text-muted-foreground">No commands available</div>
        )}
        {mainCommands.map((command) => (
          <DropdownMenuCheckboxItem
            key={command.id}
            checked={selectedCommandId === command.id}
            onCheckedChange={() =>
              setSelectedCommandId(selectedCommandId === command.id ? null : command.id)
            }
          >
            {command.name}
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default SelectCommand;
