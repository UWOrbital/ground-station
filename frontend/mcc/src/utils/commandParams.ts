import type { MainCommand } from "./types";

export interface CommandParameter {
  name: string;
  type: "int" | "float" | "boolean" | "string";
}

/**
 * Main command params and format are comma-separated strings whose lengths must match.
 * This parses them into a name and type pair per parameter
 *
 * TODO: Improve this logic and document it on the backend
 */
export function parseCommandParameters(mainCommand: MainCommand): CommandParameter[] {
  if (!mainCommand.params || !mainCommand.format) return [];

  const names = mainCommand.params.split(",").map((s) => s.trim());
  const types = mainCommand.format.split(",").map((s) => s.trim().toLowerCase());

  return names.map((name, i) => {
    const rawType = types[i] ?? "string";
    const type: CommandParameter["type"] =
      rawType === "int" || rawType === "float" || rawType === "boolean" ? rawType : "string";
    return { name, type };
  });
}
