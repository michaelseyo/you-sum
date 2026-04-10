import type { RuntimeMessage } from "./types/runtime";

function getVideoId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("v");
}

chrome.runtime.onMessage.addListener(
  (message: RuntimeMessage, _sender, sendResponse) => {
    if (message.type === "GET_VIDEO_CONTEXT") {
      sendResponse({
        title: document.title,
        url: window.location.href,
        videoId: getVideoId(),
      });
    }
  },
);
