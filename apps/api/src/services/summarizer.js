export async function summarizeTranscript(transcript) {
  return {
    headline: "Summary not implemented yet",
    bullets: [
      "Wire this file to your LLM provider.",
      "Pass transcript.text as input.",
      "Return short bullets for the popup."
    ],
    rawTranscriptPreview: transcript.text.slice(0, 140)
  };
}
