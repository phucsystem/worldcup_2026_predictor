// Pure data→view helper mapping recent finished matches into ResultChip props.
import type { RecentResult } from "@/lib/api";

export type ChipVariant = "win" | "draw" | "loss";

export interface ChipProps {
  key: string;
  letter: "W" | "D" | "L";
  variant: ChipVariant;
  label: string; // e.g. "BRA 3–1 SRB"
}

const VARIANT: Record<string, ChipVariant> = { W: "win", D: "draw", L: "loss" };

function abbr(name: string | null): string {
  if (!name) return "—";
  return name.slice(0, 3).toUpperCase();
}

export function resultsToChips(results: RecentResult[]): ChipProps[] {
  return results.map((r, i) => ({
    key: `${r.kickoff_utc ?? i}-${r.home_team ?? ""}-${r.away_team ?? ""}`,
    letter: (r.outcome as "W" | "D" | "L"),
    variant: VARIANT[r.outcome] ?? "draw",
    label: `${abbr(r.home_team)} ${r.home_score ?? "?"}–${r.away_score ?? "?"} ${abbr(r.away_team)}`,
  }));
}
