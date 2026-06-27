import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import SatelliteStatusIndicator, { type TelemetryData } from "./SatelliteStatusIndicator";

describe("SatelliteStatusIndicator", () => {
  describe("Compact Button Rendering", () => {
    it("renders the status indicator button", () => {
      render(<SatelliteStatusIndicator status="online" />);
      const button = screen.getByRole("button", { name: /Satellite status/ });
      expect(button).toBeInTheDocument();
    });

    it("displays ONLINE status label", () => {
      render(<SatelliteStatusIndicator status="online" />);
      const statusLabels = screen.getAllByText("ONLINE");
      expect(statusLabels.length).toBeGreaterThan(0);
    });

    it("displays IDLE status label", () => {
      render(<SatelliteStatusIndicator status="idle" />);
      const statusLabels = screen.getAllByText("IDLE");
      expect(statusLabels.length).toBeGreaterThan(0);
    });

    it("displays OFFLINE status label", () => {
      render(<SatelliteStatusIndicator status="offline" />);
      const statusLabels = screen.getAllByText("OFFLINE");
      expect(statusLabels.length).toBeGreaterThan(0);
    });

    it("displays ERROR status label", () => {
      render(<SatelliteStatusIndicator status="error" />);
      const statusLabels = screen.getAllByText("ERROR");
      expect(statusLabels.length).toBeGreaterThan(0);
    });

    it("has correct title attribute based on status", () => {
      render(<SatelliteStatusIndicator status="online" />);
      const button = screen.getByRole("button", { name: /Satellite status: ONLINE/i });
      expect(button).toHaveAttribute("title", "Satellite Status: ONLINE. Click for details.");
    });

    it("renders with default offline status", () => {
      render(<SatelliteStatusIndicator />);
      const statusLabels = screen.getAllByText("OFFLINE");
      expect(statusLabels.length).toBeGreaterThan(0);
    });
  });

  describe("Status Indicator Styling", () => {
    it("applies green color classes for online status", () => {
      render(<SatelliteStatusIndicator status="online" />);
      const statusText = screen.getAllByText("ONLINE")[0];
      expect(statusText).toHaveClass("text-green-400");
    });

    it("applies yellow color classes for idle status", () => {
      render(<SatelliteStatusIndicator status="idle" />);
      const statusText = screen.getAllByText("IDLE")[0];
      expect(statusText).toHaveClass("text-yellow-400");
    });

    it("applies red color classes for offline status", () => {
      render(<SatelliteStatusIndicator status="offline" />);
      const statusText = screen.getAllByText("OFFLINE")[0];
      expect(statusText).toHaveClass("text-red-400");
    });

    it("applies dark red color classes for error status", () => {
      render(<SatelliteStatusIndicator status="error" />);
      const statusText = screen.getAllByText("ERROR")[0];
      expect(statusText).toHaveClass("text-red-500");
    });
  });

  describe("Modal Functionality", () => {
    it("opens modal when button is clicked", () => {
      render(<SatelliteStatusIndicator status="online" />);
      const button = screen.getByRole("button", { name: /Satellite status: ONLINE/i });

      fireEvent.click(button);

      expect(screen.getByText("Satellite Status")).toBeInTheDocument();
    });

    it("displays modal header with status indicator", () => {
      render(<SatelliteStatusIndicator status="online" />);
      const button = screen.getByRole("button", { name: /Satellite status: ONLINE/i });

      fireEvent.click(button);

      expect(screen.getByText("Satellite Status")).toBeInTheDocument();
      const statusInModal = screen
        .getAllByText("ONLINE")
        .find((el) => el.className.includes("font-semibold"));
      expect(statusInModal).toBeInTheDocument();
    });

    it("closes modal when close button is clicked", () => {
      render(<SatelliteStatusIndicator status="online" />);
      const button = screen.getByRole("button", { name: /Satellite status: ONLINE/i });

      fireEvent.click(button);
      expect(screen.getByText("Satellite Status")).toBeInTheDocument();

      const closeButton = screen.getByLabelText("Close");
      fireEvent.click(closeButton);

      expect(screen.queryByText("Satellite Status")).not.toBeInTheDocument();
    });

    it("closes modal when backdrop is clicked", () => {
      const { container } = render(<SatelliteStatusIndicator status="online" />);
      const button = screen.getByRole("button", { name: /Satellite status: ONLINE/i });

      fireEvent.click(button);
      expect(screen.getByText("Satellite Status")).toBeInTheDocument();

      const backdrop = container.querySelector("[class*='bg-black']");
      if (backdrop) {
        fireEvent.click(backdrop);
      }

      expect(screen.queryByText("Satellite Status")).not.toBeInTheDocument();
    });
  });

  describe("Modal Content Display", () => {
    it("displays last contact time when provided", () => {
      render(<SatelliteStatusIndicator status="online" lastContact="2 min ago" />);

      const button = screen.getByRole("button");
      fireEvent.click(button);

      expect(screen.getByText("2 min ago")).toBeInTheDocument();
    });

    it("displays session duration when provided", () => {
      render(<SatelliteStatusIndicator status="online" sessionDuration="1h 23m" />);

      const button = screen.getByRole("button");
      fireEvent.click(button);

      expect(screen.getByText("1h 23m")).toBeInTheDocument();
    });

    it("displays telemetry data when provided", () => {
      const telemetryData: TelemetryData[] = [
        { label: "Battery Level", value: "85", unit: "%" },
        { label: "Temperature", value: "42", unit: "°C" },
      ];

      render(<SatelliteStatusIndicator status="online" telemetryData={telemetryData} />);

      const button = screen.getByRole("button", { name: /Satellite status: ONLINE/i });
      fireEvent.click(button);

      expect(screen.getByText("Battery Level")).toBeInTheDocument();
      expect(screen.getByText("85")).toBeInTheDocument();
      expect(screen.getByText("Temperature")).toBeInTheDocument();
      expect(screen.getByText("42")).toBeInTheDocument();
    });

    it("displays no telemetry message when no data provided", () => {
      render(<SatelliteStatusIndicator status="online" />);

      const button = screen.getByRole("button");
      fireEvent.click(button);

      expect(screen.getByText("No telemetry data available")).toBeInTheDocument();
    });

    it("displays multiple telemetry items correctly", () => {
      const telemetryData: TelemetryData[] = [
        { label: "Battery Level", value: "85", unit: "%" },
        { label: "Temperature", value: "42", unit: "°C" },
        { label: "Signal Strength", value: "Strong" },
        { label: "Altitude", value: "450", unit: "km" },
      ];

      render(<SatelliteStatusIndicator status="online" telemetryData={telemetryData} />);

      const button = screen.getByRole("button");
      fireEvent.click(button);

      expect(screen.getByText("Battery Level")).toBeInTheDocument();
      expect(screen.getByText("Temperature")).toBeInTheDocument();
      expect(screen.getByText("Signal Strength")).toBeInTheDocument();
      expect(screen.getByText("Altitude")).toBeInTheDocument();
    });

    it("displays telemetry without unit when unit is empty string", () => {
      const telemetryData: TelemetryData[] = [
        { label: "Signal Strength", value: "Strong", unit: "" },
      ];

      render(<SatelliteStatusIndicator status="online" telemetryData={telemetryData} />);

      const button = screen.getByRole("button");
      fireEvent.click(button);

      expect(screen.getByText("Strong")).toBeInTheDocument();
    });
  });

  describe("Modal Status Display", () => {
    it("displays correct status in modal for online state", () => {
      render(<SatelliteStatusIndicator status="online" />);

      const button = screen.getByRole("button", { name: /Satellite status: ONLINE/i });
      fireEvent.click(button);

      const statusLabels = screen.getAllByText("ONLINE");
      expect(statusLabels.length).toBeGreaterThan(1);
    });

    it("displays correct status in modal for idle state", () => {
      render(<SatelliteStatusIndicator status="idle" />);

      const button = screen.getByRole("button", { name: /Satellite status: IDLE/i });
      fireEvent.click(button);

      const statusLabels = screen.getAllByText("IDLE");
      expect(statusLabels.length).toBeGreaterThan(1);
    });

    it("displays correct status in modal for offline state", () => {
      render(<SatelliteStatusIndicator status="offline" />);

      const button = screen.getByRole("button", { name: /Satellite status: OFFLINE/i });
      fireEvent.click(button);

      const statusLabels = screen.getAllByText("OFFLINE");
      expect(statusLabels.length).toBeGreaterThan(1);
    });

    it("displays correct status in modal for error state", () => {
      render(<SatelliteStatusIndicator status="error" />);

      const button = screen.getByRole("button", { name: /Satellite status: ERROR/i });
      fireEvent.click(button);

      const statusLabels = screen.getAllByText("ERROR");
      expect(statusLabels.length).toBeGreaterThan(1);
    });
  });

  describe("Accessibility", () => {
    it("has proper aria-label on button", () => {
      render(<SatelliteStatusIndicator status="online" />);
      const button = screen.getByRole("button", {
        name: /Satellite status: ONLINE/i,
      });
      expect(button).toHaveAttribute("aria-label");
    });

    it("has close button with aria-label", () => {
      render(<SatelliteStatusIndicator status="online" />);
      const button = screen.getByRole("button", {
        name: /Satellite status: ONLINE/i,
      });

      fireEvent.click(button);

      const closeButton = screen.getByLabelText("Close");
      expect(closeButton).toBeInTheDocument();
    });
  });

  describe("Status Updates", () => {
    it("updates display when status prop changes from online to offline", () => {
      const { rerender } = render(<SatelliteStatusIndicator status="online" />);

      expect(screen.getByText("ONLINE")).toBeInTheDocument();

      rerender(<SatelliteStatusIndicator status="offline" />);

      expect(screen.queryByText("ONLINE")).not.toBeInTheDocument();
      expect(screen.getByText("OFFLINE")).toBeInTheDocument();
    });

    it("updates telemetry data when data prop changes", () => {
      const initialData: TelemetryData[] = [{ label: "Battery", value: "85", unit: "%" }];

      const { rerender } = render(
        <SatelliteStatusIndicator status="online" telemetryData={initialData} />,
      );

      const button = screen.getByRole("button");
      fireEvent.click(button);

      expect(screen.getByText("Battery")).toBeInTheDocument();

      const updatedData: TelemetryData[] = [{ label: "Temperature", value: "42", unit: "°C" }];

      rerender(<SatelliteStatusIndicator status="online" telemetryData={updatedData} />);

      expect(screen.queryByText("Battery")).not.toBeInTheDocument();
      expect(screen.getByText("Temperature")).toBeInTheDocument();
    });
  });
});
