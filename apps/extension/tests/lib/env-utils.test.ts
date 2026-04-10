import { describe, expect, it } from "vitest";
import { normalizeEnv } from "../../src/lib/env-utils.ts";

describe("normalizeEnv", () => {
  it("returns undefined for missing values", () => {
    expect(normalizeEnv(undefined)).toBeUndefined();
  });

  it("returns undefined for blank values", () => {
    expect(normalizeEnv("")).toBeUndefined();
    expect(normalizeEnv("   ")).toBeUndefined();
  });

  it('returns undefined for "undefined" values with extra whitespace', () => {
    expect(normalizeEnv("undefined")).toBeUndefined();
    expect(normalizeEnv(" undefined ")).toBeUndefined();
  });

  it('returns undefined for "null" placeholder values', () => {
    expect(normalizeEnv("null")).toBeUndefined();
    expect(normalizeEnv("NULL")).toBeUndefined();
  });

  it("returns trimmed values for valid env strings", () => {
    expect(normalizeEnv(" value ")).toBe("value");
  });
});
