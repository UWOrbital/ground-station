import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { createQueryWrapper } from "@/hooks/testUtils";
import App from "./App";

describe("App", () => {
  it("opens password recovery directly by its route", () => {
    render(
      <MemoryRouter initialEntries={["/forgot-password"]}>
        <App />
      </MemoryRouter>,
      { wrapper: createQueryWrapper() },
    );
    expect(screen.getByRole("heading", { name: "Forgot Your Password?" })).toBeInTheDocument();
  });

  it("navigates from login to password recovery and back", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <App />
      </MemoryRouter>,
      { wrapper: createQueryWrapper() },
    );
    const link = screen.getByRole("link", { name: "Forgot Your Password?" });
    expect(link).toHaveAttribute("href", "/forgot-password");
    await user.click(link);
    expect(screen.getByRole("heading", { name: "Forgot Your Password?" })).toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: "Back to Login" }));
    expect(screen.getByRole("heading", { name: "Login to your ARO Account" })).toBeInTheDocument();
  });

  it("renders the App component", () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    screen.debug(); // prints out the jsx in the App component unto the command line
  });
});
