import { getTranscript } from "../services/transcript.js";
import { summarizeTranscript } from "../services/summarizer.js";

async function readJsonBody(req) {
  const chunks = [];

  for await (const chunk of req) {
    chunks.push(chunk);
  }

  if (chunks.length === 0) {
    return {};
  }

  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

export async function summarizeVideo(req, res) {
  try {
    const body = await readJsonBody(req);
    const videoId = body.videoId;

    if (!videoId) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "videoId is required" }));
      return;
    }

    const transcript = await getTranscript(videoId);
    const summary = await summarizeTranscript(transcript);

    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ videoId, transcript, summary }));
  } catch (error) {
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Failed to summarize video" }));
  }
}
