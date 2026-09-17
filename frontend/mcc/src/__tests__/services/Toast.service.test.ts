import { describe, it, expect, vi } from "vitest";
import { toast } from "react-toastify";
import toastService from "@/services/Toast.service";

vi.mock("react-toastify", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const shared = { position: "top-right", autoClose: 4900, closeOnClick: true, theme: "dark" };

describe("toastService", () => {
  it("shows a green success toast", () => {
    toastService.success("Saved");
    expect(toast.success).toHaveBeenCalledWith(
      "Saved",
      expect.objectContaining({ ...shared, progressClassName: "bg-green-500" }),
    );
  });

  it("shows a red error toast", () => {
    toastService.error("Failed");
    expect(toast.error).toHaveBeenCalledWith(
      "Failed",
      expect.objectContaining({ ...shared, progressClassName: "bg-red-500" }),
    );
  });
});
