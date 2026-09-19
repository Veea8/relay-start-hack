import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("Relay interface", () => {
  it("loads all three customer screens and mock decisions", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: /set the boundaries/i })).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: /approval inbox/i })[0]);
    expect(await screen.findByText("RainThread")).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: /decision log/i })[0]);
    expect(await screen.findByText("Giftly Market")).toBeInTheDocument();
    expect(screen.getByText("Alpine Basket")).toBeInTheDocument();
  });

  it("compiles and confirms a policy", async () => {
    render(<App />);
    await screen.findByRole("heading", { name: /set the boundaries/i });
    await userEvent.click(screen.getByRole("button", { name: /build policy/i }));
    expect(await screen.findByText("Limit per order")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /confirm policy/i }));
    await waitFor(() => expect(screen.getByText(/policy confirmed/i)).toBeInTheDocument());
  });

  it("resolves a pending purchase only once", async () => {
    render(<App />);
    await screen.findByRole("heading", { name: /set the boundaries/i });
    await userEvent.click(screen.getAllByRole("button", { name: /approval inbox/i })[0]);
    await userEvent.click(await screen.findByRole("button", { name: /approve once/i }));
    expect(await screen.findByText(/all caught up/i)).toBeInTheDocument();
  });
});
