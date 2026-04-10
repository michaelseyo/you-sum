export function normalizeEnv(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  const normalized = trimmed?.toLowerCase();

  if (!trimmed || normalized === "undefined" || normalized === "null") {
    return undefined;
  }
  return trimmed;
}
