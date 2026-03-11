function getVideoId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("v");
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "GET_VIDEO_CONTEXT") {
    sendResponse({
      videoId: getVideoId(),
      url: window.location.href,
      title: document.title
    });
  }
});
