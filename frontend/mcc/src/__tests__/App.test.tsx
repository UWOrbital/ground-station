import { describe, it, expect } from "vitest";
import { render, waitFor, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "@/App";

describe("App", () => {
  it("should render without crashing", async () => {
    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });
  });
});
