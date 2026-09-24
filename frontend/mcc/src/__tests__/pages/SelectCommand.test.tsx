import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SelectCommand from "@/pages/SelectCommand";
import type { MainCommand } from "@/utils/types";

const command = (id: number, name: string): MainCommand => ({
  id,
  name,
  params: null,
  format: null,
  data_size: 0,
  total_size: 0,
  priority: 0,
});

const commands = [command(1, "PING"), command(2, "SET_RATE")];

const renderMenu = (mainCommands: MainCommand[], selectedCommandId: number | null) => {
  const setSelectedCommandId = vi.fn();
  render(
    <SelectCommand
      mainCommands={mainCommands}
      selectedCommandId={selectedCommandId}
      setSelectedCommandId={setSelectedCommandId}
    />,
  );
  return setSelectedCommandId;
};

const openMenu = () => userEvent.click(screen.getByRole("button"));

describe("SelectCommand", () => {
  it("lists every main command, checking the selected one", async () => {
    renderMenu(commands, 2);
    await openMenu();
    expect(screen.getByRole("menuitemcheckbox", { name: "PING" })).toHaveAttribute(
      "aria-checked",
      "false",
    );
    expect(screen.getByRole("menuitemcheckbox", { name: "SET_RATE" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
  });

  it("says when there are no commands", async () => {
    renderMenu([], null);
    await openMenu();
    expect(screen.getByText("No commands available")).toBeInTheDocument();
  });

  it("selects an unselected command", async () => {
    const set = renderMenu(commands, null);
    await openMenu();
    await userEvent.click(screen.getByRole("menuitemcheckbox", { name: "SET_RATE" }));
    expect(set).toHaveBeenCalledWith(2);
  });

  it("deselects the command that is already selected", async () => {
    const set = renderMenu(commands, 2);
    await openMenu();
    await userEvent.click(screen.getByRole("menuitemcheckbox", { name: "SET_RATE" }));
    expect(set).toHaveBeenCalledWith(null);
  });
});
