import type { Metadata } from "next";
import { getStandings, getKnockout } from "@/lib/api";

export const metadata: Metadata = {
  title: "Group Standings",
  description:
    "Live Group A–L standings for the 2026 World Cup — points, goal difference, form and qualification scenarios for all 48 teams.",
  alternates: { canonical: "/standings" },
};
import StandingsView from "@/components/standings-view";

export const dynamic = "force-dynamic";

export default async function StandingsPage() {
  const [snapshot, knockout] = await Promise.all([getStandings(), getKnockout()]);

  const snapshotLabel = snapshot?.snapshot_date
    ? new Date(snapshot.snapshot_date + "T00:00:00").toLocaleDateString("en-AU", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : null;

  return (
    <div className="px-6 py-8" style={{ maxWidth: "1120px", margin: "0 auto" }}>
      <div className="flex items-baseline justify-between mb-6 flex-wrap gap-2">
        <h1 className="text-2xl font-bold" style={{ color: "#FFFFFF" }}>
          Standings
        </h1>
        {snapshotLabel && (
          <p
            className="text-xs font-semibold uppercase tracking-widest"
            style={{ color: "#6B7A9E", letterSpacing: "0.06em" }}
          >
            Snapshot: {snapshotLabel}
          </p>
        )}
      </div>

      <StandingsView snapshot={snapshot} knockout={knockout} />
    </div>
  );
}
