import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../src/popup/App";

const chromeHelpers = vi.hoisted(() => ({
  getActiveTab: vi.fn(),
  getVideoContext: vi.fn(),
  sendRuntimeMessage: vi.fn(),
}));

const apiHelpers = vi.hoisted(() => ({
  summarizeVideo: vi.fn(),
}));

vi.mock("../../src/lib/chrome", () => chromeHelpers);
vi.mock("../../src/lib/api", () => apiHelpers);

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows the signed-out state when no auth state is available", async () => {
    chromeHelpers.sendRuntimeMessage.mockResolvedValue({
      authState: null,
      ok: true,
    });

    render(<App />);

    expect(
      await screen.findByText("Sign in with Google to use your backend."),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Sign in with Google" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Sign out" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Summarize this video" }),
    ).toBeDisabled();
  });

  it("shows the signed-in state when auth is available", async () => {
    chromeHelpers.sendRuntimeMessage.mockResolvedValue({
      authState: {
        accessToken: "token",
        expiresAt: Date.now() + 60_000,
        user: {
          email: "test@example.com",
        },
      },
      ok: true,
    });

    render(<App />);

    expect(
      await screen.findByText("Signed in as test@example.com"),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Summarize this video" }),
      ).not.toBeDisabled();
    });
  });
});
