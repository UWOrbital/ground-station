import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { createQueryWrapper } from "@/hooks/testUtils";
import { AuthProvider } from "@/contexts/AuthContext";
import App from "./App";

describe("App", () => {
  it("opens password recovery directly by its route", () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/forgot-password"]}>
          <App />
        </MemoryRouter>
      </AuthProvider>,
      { wrapper: createQueryWrapper() },
    );
    expect(screen.getByRole("heading", { name: "Reset your password" })).toBeInTheDocument();
  });

  it("navigates from login to password recovery and back", async () => {
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/login"]}>
          <App />
        </MemoryRouter>
      </AuthProvider>,
      { wrapper: createQueryWrapper() },
    );
    const link = screen.getByRole("link", { name: "Forgot Your Password?" });
    expect(link).toHaveAttribute("href", "/forgot-password");
    await user.click(link);
    expect(screen.getByRole("heading", { name: "Reset your password" })).toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: "Back to login" }));
    expect(screen.getByRole("heading", { name: "Login to your ARO Account" })).toBeInTheDocument();
  });

  it("renders the App component", () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <App />
        </MemoryRouter>
      </AuthProvider>,
      { wrapper: createQueryWrapper() },
    );

    screen.debug(); // prints out the jsx in the App component unto the command line
  });
});
