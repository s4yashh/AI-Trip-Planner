import type { Metadata } from "next";
import { FlightsClient } from "@/components/flights/FlightsClient";

export const metadata: Metadata = {title: "Flights"};

type Params = Record<string, string | string[] | undefined>;

function text(params: Params, key: string) {
  const value = params[key];
  return typeof value === "string" && value.trim() ? value.trim().slice(0, 100) : undefined;
}

export default async function FlightsPage({searchParams}: {searchParams: Promise<Params>}) {
  const params = await searchParams;
  const adults = Number(text(params, "adults"));
  const defaults = {
    from: text(params, "from"), to: text(params, "to"), depart: text(params, "depart"), returnDate: text(params, "return"),
    adults: Number.isInteger(adults) && adults > 0 && adults <= 9 ? adults : undefined,
  };
  return <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6"><FlightsClient defaults={defaults}/></main>;
}
