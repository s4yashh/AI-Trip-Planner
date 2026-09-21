import { describe, expect, it } from "vitest";
import { formatDuration, formatMoney } from "../lib/money";

describe("formatMoney", () => {
  it("should format INR with the rupee symbol", () => {
    expect(formatMoney(30000, "INR")).toBe("\u20b930,000");
  });

  it("should format USD with the dollar symbol", () => {
    expect(formatMoney(250, "USD")).toBe("$250");
  });

  it("should default to INR when currency is omitted", () => {
    expect(formatMoney(1000)).toBe("\u20b91,000");
  });

  it("should render fractional amounts", () => {
    expect(formatMoney(123.45, "USD")).toBe("$123.45");
  });

  it("should handle null and undefined", () => {
    expect(formatMoney(null)).toBe("—");
    expect(formatMoney(undefined)).toBe("—");
  });
});

describe("formatDuration", () => {
  it("should format integer hours without decimals", () => {
    expect(formatDuration(2)).toBe("2 hours");
  });

  it("should format fractional hours", () => {
    expect(formatDuration(1.5)).toBe("1.5 hours");
  });

  it("should return an em dash for zero", () => {
    expect(formatDuration(0)).toBe("—");
  });
});