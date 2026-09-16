import { describe, it, expect } from "vitest";
import { parseCommandParameters } from "@/utils/commandParams";
import type { MainCommand } from "@/utils/types";

const cmd = (params: string | null, format: string | null): MainCommand => ({
  id: 1,
  name: "CMD",
  params,
  format,
  data_size: 0,
  total_size: 0,
  priority: 0,
});

describe("parseCommandParameters", () => {
  it("returns no parameters when params or format is missing", () => {
    expect(parseCommandParameters(cmd(null, null))).toEqual([]);
    expect(parseCommandParameters(cmd("rate", null))).toEqual([]);
    expect(parseCommandParameters(cmd(null, "int"))).toEqual([]);
  });

  it("pairs each trimmed name with its lowercased type", () => {
    expect(
      parseCommandParameters(cmd("rate, enabled ,gain,label", "INT,boolean, Float ,string")),
    ).toEqual([
      { name: "rate", type: "int" },
      { name: "enabled", type: "boolean" },
      { name: "gain", type: "float" },
      { name: "label", type: "string" },
    ]);
  });

  it("falls back to string for unknown or missing types", () => {
    expect(parseCommandParameters(cmd("a,b", "uint8"))).toEqual([
      { name: "a", type: "string" },
      { name: "b", type: "string" },
    ]);
  });
});
