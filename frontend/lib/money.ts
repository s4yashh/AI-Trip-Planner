import type { Currency } from "@/types/trip";

export function formatMoney(
  amount: number | null | undefined,
  currency: Currency | string = "INR",
): string {
  if (amount === null || amount === undefined || Number.isNaN(amount)) {
    return "—";
  }
  const symbol = currency.toUpperCase() === "INR" ? "\u20b9" : "$";
  const locale = currency.toUpperCase() === "INR" ? "en-IN" : "en-US";
  const isWhole = Math.abs(amount % 1) < 1e-9;
  const digits = isWhole ? 0 : 2;
  return `${symbol}${Math.abs(amount).toLocaleString(locale, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

export function formatDuration(hours: number): string {
  if (!hours) return "—";
  return `${Number.isInteger(hours) ? hours : hours.toFixed(1)} hours`;
}