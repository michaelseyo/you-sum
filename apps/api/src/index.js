import http from "node:http";
import { summarizeVideo } from "./routes/summarize.js";
import { getEnv } from "./lib/env.js";

const env = getEnv();

const server = http.createServer(async (req, res) => {
  if (req.method === "POST" && req.url === "/summarize") {
    return summarizeVideo(req, res);
  }

  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ status: "ok", service: "you-sum-api", port: env.port }));
});

server.listen(env.port, () => {
  console.log(`you-sum API listening on http://localhost:${env.port}`);
});
