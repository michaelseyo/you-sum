const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const summarizeButton = document.getElementById("summarize-button");

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function getVideoContext(tabId) {
  return chrome.tabs.sendMessage(tabId, { type: "GET_VIDEO_CONTEXT" });
}

async function summarizeVideo(videoId) {
  const response = await fetch("http://localhost:8787/summarize", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ videoId })
  });

  if (!response.ok) {
    throw new Error("API request failed");
  }

  return response.json();
}

summarizeButton.addEventListener("click", async () => {
  statusEl.textContent = "Reading current tab...";
  resultEl.textContent = "Loading...";

  try {
    const tab = await getActiveTab();

    if (!tab?.id) {
      throw new Error("No active tab found");
    }

    const context = await getVideoContext(tab.id);

    if (!context?.videoId) {
      throw new Error("Open a YouTube video first");
    }

    statusEl.textContent = `Summarizing ${context.videoId}...`;
    const data = await summarizeVideo(context.videoId);

    resultEl.textContent = JSON.stringify(data.summary, null, 2);
    statusEl.textContent = "Summary loaded";
  } catch (error) {
    statusEl.textContent = "Unable to summarize video";
    resultEl.textContent = error.message;
  }
});
