"use client";

import { useState } from "react";
import type { StandingsSnapshot, KnockoutBracket } from "@/lib/api";
import StandingsTable from "@/components/standings-table";
import KnockoutBracketView from "@/components/knockout-bracket";
import EmptyState from "@/components/empty-state";

type View = "groups" | "knockout";

interface Props {
  snapshot: StandingsSnapshot | null;
  knockout: KnockoutBracket;
}

export default function StandingsView({ snapshot, knockout }: Props) {
  // The Knockout tab unlocks itself once the bracket endpoint returns rounds —
  // no redeploy needed when Round of 16 fixtures land in the DB.
  const hasKnockout = knockout.rounds.length > 0;
  const [view, setView] = useState<View>("groups");
  const active: View = hasKnockout ? view : "groups";

  return (
    <>
      <div className="flex gap-2 mb-8" role="tablist" aria-label="View toggle">
        <button
          role="tab"
          aria-selected={active === "groups"}
          onClick={() => setView("groups")}
          className="px-4 py-2 text-sm font-semibold rounded-full"
          style={{
            backgroundColor: active === "groups" ? "#2D6BF6" : "#0A1B3D",
            color: active === "groups" ? "#FFFFFF" : "#A9B6D4",
            border: active === "groups" ? "none" : "1px solid #1E3157",
            cursor: "pointer",
          }}
        >
          Groups
        </button>
        <button
          role="tab"
          aria-selected={active === "knockout"}
          aria-disabled={!hasKnockout}
          onClick={() => hasKnockout && setView("knockout")}
          className="px-4 py-2 text-sm font-medium rounded-full"
          style={{
            backgroundColor: active === "knockout" ? "#2D6BF6" : "#0A1B3D",
            color:
              active === "knockout"
                ? "#FFFFFF"
                : hasKnockout
                  ? "#A9B6D4"
                  : "#6B7A9E",
            border: active === "knockout" ? "none" : "1px solid #1E3157",
            cursor: hasKnockout ? "pointer" : "not-allowed",
          }}
          title={hasKnockout ? undefined : "Available once knockout stage begins"}
        >
          Knockout
        </button>
      </div>

      {active === "knockout" ? (
        <KnockoutBracketView bracket={knockout} />
      ) : !snapshot || snapshot.groups.length === 0 ? (
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
    </>
  );
}
