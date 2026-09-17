import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentProps } from "react";
import SendCommand from "@/pages/SendCommand";
import { useCreateCommand } from "@/hooks/useCommands";
import { ApiError } from "@/lib/apiClient";
import type { MainCommand } from "@/utils/types";

vi.mock("@/hooks/useCommands", () => ({ useCreateCommand: vi.fn() }));

const command = (params: string | null, format: string | null): MainCommand => ({
  id: 7,
  name: "SET_RATE",
  params,
  format,
  data_size: 4,
  total_size: 12,
  priority: 1,
});

const FAR_FUTURE = "2099-01-01T00:00:00Z";
const mutateAsync = vi.fn();

const renderSend = (overrides: Partial<ComponentProps<typeof SendCommand>> = {}) => {
  const props = {
    mainCommand: command("rate,label", "int,string"),
    selectedSessionId: "ses-1",
    sessionStartTime: FAR_FUTURE,
    setSelectedCommandId: vi.fn(),
    onSubmitted: vi.fn(),
    ...overrides,
  };
  return { ...props, ...render(<SendCommand {...props} />) };
};

const submit = () => userEvent.click(screen.getByRole("button", { name: "Submit" }));

describe("SendCommand", () => {
  beforeAll(() => {
    // jsdom lacks these; Radix Select calls them when opening
    Element.prototype.hasPointerCapture = () => false;
    Element.prototype.scrollIntoView = () => {};
  });

  beforeEach(() => {
    mutateAsync.mockReset();
    vi.mocked(useCreateCommand).mockReturnValue({ mutateAsync } as unknown as ReturnType<
      typeof useCreateCommand
    >);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders nothing without a main command", () => {
    const { container } = renderSend({ mainCommand: null });
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the command details and an input per parameter", () => {
    renderSend();
    expect(screen.getByText("SET_RATE")).toBeInTheDocument();
    expect(
      screen.getByText(/Command ID: 7 \| Data Size: 4 \| Total Size: 12 bytes/),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("rate")).toHaveAttribute("placeholder", "Enter integer");
    expect(screen.getByLabelText("label")).toHaveAttribute("placeholder", "Enter text");
  });

  it("keeps Submit disabled until every parameter is filled", async () => {
    renderSend();
    const button = screen.getByRole("button", { name: "Submit" });
    expect(button).toBeDisabled();

    await userEvent.type(screen.getByLabelText("rate"), "5");
    expect(button).toBeDisabled();

    await userEvent.type(screen.getByLabelText("label"), "fast");
    expect(button).toBeEnabled();
  });

  it("submits params in order with the sequence index, then resets and notifies", async () => {
    mutateAsync.mockResolvedValue({});
    const { onSubmitted } = renderSend();

    await userEvent.type(screen.getByLabelText("rate"), "5");
    await userEvent.type(screen.getByLabelText("label"), "fast");
    await userEvent.type(screen.getByLabelText("Sequence index (optional)"), "2");
    await submit();

    expect(mutateAsync).toHaveBeenCalledWith({
      type_: 7,
      params: "5,fast",
      session_id: "ses-1",
      sequence_index: 2,
    });
    expect(await screen.findByText("Success, command submitted!")).toBeInTheDocument();
    expect(screen.getByLabelText("rate")).toHaveValue(null);
    expect(screen.getByLabelText("label")).toHaveValue("");
    expect(screen.getByLabelText("Sequence index (optional)")).toHaveValue(null);
    expect(onSubmitted).toHaveBeenCalledOnce();
  });

  it("omits params and sequence index when the command takes none", async () => {
    mutateAsync.mockResolvedValue({});
    renderSend({ mainCommand: command(null, null) });
    await submit();
    expect(mutateAsync).toHaveBeenCalledWith({
      type_: 7,
      params: undefined,
      session_id: "ses-1",
      sequence_index: undefined,
    });
  });

  it("submits a boolean parameter picked from the select", async () => {
    mutateAsync.mockResolvedValue({});
    renderSend({ mainCommand: command("enabled", "boolean") });
    expect(screen.getByRole("button", { name: "Submit" })).toBeDisabled();

    await userEvent.click(screen.getByRole("combobox"));
    await userEvent.click(await screen.findByRole("option", { name: "True" }));
    await submit();

    expect(mutateAsync).toHaveBeenCalledWith(expect.objectContaining({ params: "true" }));
  });

  it("blocks submission inside the session lockout window", async () => {
    const { onSubmitted } = renderSend({
      mainCommand: command(null, null),
      sessionStartTime: new Date().toISOString(),
    });
    await submit();
    expect(screen.getByText(/Session is locked/)).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
    expect(onSubmitted).not.toHaveBeenCalled();
  });

  it("rejects submission when no session is selected", async () => {
    renderSend({ mainCommand: command(null, null), selectedSessionId: null });
    await submit();
    expect(screen.getByText(/Form invalid/)).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it("shows the lockout alert when the backend answers 409", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    mutateAsync.mockRejectedValue(new ApiError(409, "Session locked"));
    const { onSubmitted } = renderSend({ mainCommand: command(null, null) });
    await submit();
    expect(await screen.findByText(/Session is locked/)).toBeInTheDocument();
    expect(onSubmitted).not.toHaveBeenCalled();
  });

  it("shows an unknown-error alert for any other failure", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    mutateAsync.mockRejectedValue(new ApiError(500, "boom"));
    renderSend({ mainCommand: command(null, null) });
    await submit();
    expect(await screen.findByText(/unknown error occurred/)).toBeInTheDocument();
  });

  it("disables both buttons while the command is being sent", async () => {
    mutateAsync.mockReturnValue(new Promise(() => {}));
    renderSend({ mainCommand: command(null, null) });
    await submit();
    expect(screen.getByRole("button", { name: "Submit" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });

  it("Cancel closes the form by clearing the selected command", async () => {
    const { setSelectedCommandId } = renderSend();
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(setSelectedCommandId).toHaveBeenCalledWith(null);
  });
});
