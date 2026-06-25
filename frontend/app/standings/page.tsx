import type { Metadata } from "next";
import { getStandings } from "@/lib/api";

export const metadata: Metadata = {
  title: "Group Standings",
  description:
    "Live Group A–L standings for the 2026 World Cup — points, goal difference, form and qualification scenarios for all 48 teams.",
  alternates: { canonical: "/standings" },
};
import StandingsTable from "@/components/standings-table";
import EmptyState from "@/components/empty-state";

export const dynamic = "force-dynamic";

export default async function StandingsPage() {
  const snapshot = await getStandings();

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

      {/* Knockout toggle — empty-stated stub until knockout data exists */}
      <div className="flex gap-2 mb-8" role="tablist" aria-label="View toggle">
        <button
          role="tab"
          aria-selected="true"
          className="px-4 py-2 text-sm font-semibold rounded-full"
          style={{
            backgroundColor: "#2D6BF6",
            color: "#FFFFFF",
            border: "none",
            cursor: "default",
          }}
        >
          Groups
        </button>
        <button
          role="tab"
          aria-selected="false"
          aria-disabled="true"
          className="px-4 py-2 text-sm font-medium rounded-full"
          style={{
            backgroundColor: "#0A1B3D",
            color: "#6B7A9E",
            border: "1px solid #1E3157",
            cursor: "not-allowed",
          }}
          title="Available once knockout stage begins"
        >
          Knockout
        </button>
      </div>

      {!snapshot || snapshot.groups.length === 0 ? (
        <EmptyState
          message="Standings will appear once match data is available."
          subtext="Check back after the first group stage matches."
        />
      ) : (
        <div className="grid gap-6 grid-cols-1">
          {snapshot.groups.map((g) => (
            <StandingsTable key={g.group_name} groupName={g.group_name} rows={g.rows} />
          ))}
        </div>
      )}
    </div>
  );
}
