import {GroupTripClient} from "@/components/group-trip/GroupTripClient";

export default async function GroupPlanPage({searchParams}: {
  searchParams: Promise<{group?: string | string[]}>;
}) {
  const params = await searchParams;
  const initialGroupId = typeof params.group === "string" ? params.group : undefined;
  return <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6"><GroupTripClient initialGroupId={initialGroupId}/></main>;
}
