export function getEnv() {
  return {
    port: Number(process.env.PORT || 8787),
    openAiApiKey: process.env.OPENAI_API_KEY || ""
  };
}
