import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { createQueryWrapper } from "@/__tests__/testUtils";

function Probe() {
  const { isAuthenticated, isLoading, recheck } = useAuth();
  return (
    <>
      <p>{isLoading ? "loading" : isAuthenticated ? "signed in" : "signed out"}</p>
      <button onClick={recheck}>recheck</button>
    </>
  );
}

const renderProbe = () =>
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
    { wrapper: createQueryWrapper() },
  );

const pingReturns = (ok: boolean) =>
  vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok } as Response);

describe("AuthContext", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("is loading, then signed in when the auth ping succeeds", async () => {
    pingReturns(true);
    renderProbe();
    expect(screen.getByText("loading")).toBeInTheDocument();
    expect(await screen.findByText("signed in")).toBeInTheDocument();
  });

  it("is signed out when the auth ping fails", async () => {
    pingReturns(false);
    renderProbe();
    expect(await screen.findByText("signed out")).toBeInTheDocument();
  });

  it("recheck pings again and picks up a new session", async () => {
    const fetchSpy = pingReturns(false);
    renderProbe();
    await screen.findByText("signed out");

    fetchSpy.mockResolvedValue({ ok: true } as Response);
    await userEvent.click(screen.getByRole("button", { name: "recheck" }));

    expect(await screen.findByText("signed in")).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("throws when used outside AuthProvider", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Probe />)).toThrow("useAuth must be used within AuthProvider");
  });
});
