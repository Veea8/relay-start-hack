import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import App from "./App";
import { api } from "./api";
import { mockPolicy } from "./mockData";

describe("Relay interface", () => {
  it("loads all three customer screens and mock decisions", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: "RainThread" })).toBeInTheDocument();
    expect(screen.getByText(/prototype data/i)).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: /^policy$/i })[0]);
    expect(await screen.findByRole("heading", { name: /set the boundaries/i })).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: /decision log/i })[0]);
    expect(await screen.findByText("Giftly Market")).toBeInTheDocument();
    expect(screen.getByText("Alpine Basket")).toBeInTheDocument();
  });

  it("compiles and confirms a policy", async () => {
    render(<App />);
    await userEvent.click((await screen.findAllByRole("button", { name: /^policy$/i }))[0]);
    await screen.findByRole("heading", { name: /set the boundaries/i });
    await userEvent.click(screen.getByRole("button", { name: /build policy/i }));
    expect(await screen.findByText("Limit per order")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /confirm policy/i }));
    await waitFor(() => expect(screen.getByText(/policy confirmed/i)).toBeInTheDocument());
  });

  it("resolves a pending purchase only once", async () => {
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: /approve once/i }));
    expect(await screen.findByText(/audit log has been updated/i)).toBeInTheDocument();
    expect(await screen.findByText(/all caught up/i)).toBeInTheDocument();
  });

  it("restores the active policy after a page load", async () => {
    const restored = { ...structuredClone(mockPolicy), mandate_id: "TM-RESTORED", status: "active" as const };
    const currentPolicy = vi.spyOn(api, "currentPolicy").mockResolvedValueOnce(restored);
    render(<App />);
    await userEvent.click((await screen.findAllByRole("button", { name: /^policy$/i }))[0]);
    expect(await screen.findByDisplayValue(restored.instruction)).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /start offline run/i })).toBeInTheDocument();
    currentPolicy.mockRestore();
  });
});
