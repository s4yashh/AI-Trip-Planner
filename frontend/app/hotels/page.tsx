import type { Metadata } from "next";
import { HotelsClient } from "@/components/hotels/HotelsClient";

export const metadata: Metadata = {title: "Hotels"};

type Params = Record<string, string | string[] | undefined>;

function text(params: Params, key: string) {
  const value = params[key];
  return typeof value === "string" && value.trim() ? value : undefined;
}

function count(params: Params, key: string) {
  const value = Number(text(params, key));
  return Number.isInteger(value) && value > 0 ? value : undefined;
}

export default async function HotelsPage({searchParams}: {searchParams: Promise<Params>}) {
  const params = await searchParams;
  const currency = text(params, "currency");
  const defaults = {
    destination: text(params, "destination"), checkIn: text(params, "check_in"), checkOut: text(params, "check_out"),
    adults: count(params, "adults"), rooms: count(params, "rooms"),
    currency: currency === "USD" || currency === "INR" ? currency : undefined,
  } as const;
  return <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6"><HotelsClient defaults={defaults}/></main>;
}
