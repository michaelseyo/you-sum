import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../src/popup/App";

const chromeHelpers = vi.hoisted(() => ({
  getActiveTab: vi.fn(),
  getVideoContext: vi.fn(),
  sendRuntimeMessage: vi.fn(),
}));

const apiHelpers = vi.hoisted(() => ({
  summarizeVideoStream: vi.fn(),
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

  it("renders streamed summary chunks as they arrive", async () => {
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
    chromeHelpers.getActiveTab.mockResolvedValue({ id: 1 });
    chromeHelpers.getVideoContext.mockResolvedValue({
      title: "Video",
      url: "https://youtube.com/watch?v=video-1",
      videoId: "video-1",
    });
    apiHelpers.summarizeVideoStream.mockImplementation(
      async (_videoId, _accessToken, onEvent) => {
        onEvent({ message: "Writing summary...", type: "status" });
        onEvent({ text: "Hello", type: "delta" });
        onEvent({ text: " world", type: "delta" });
        onEvent({ cached: false, prompt_version: "v1", type: "done" });
      },
    );

    render(<App />);

    const summarizeButton = await screen.findByRole("button", {
      name: "Summarize this video",
    });
    await waitFor(() => {
      expect(summarizeButton).not.toBeDisabled();
    });
    fireEvent.click(summarizeButton);

    expect(await screen.findByText("Hello world")).toBeInTheDocument();
    expect(screen.getByText("Summary loaded")).toBeInTheDocument();
    expect(apiHelpers.summarizeVideoStream).toHaveBeenCalledWith(
      "video-1",
      "token",
      expect.any(Function),
    );
  });
});
