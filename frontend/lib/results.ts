// Pure data→view helper mapping recent finished matches into ResultChip props.
import type { GroupStandings, RecentResult } from "@/lib/api";
import { dateKey, kickoffDayLabel } from "@/lib/time";

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

export interface ResultWidgetRow {
  key: string;
  fixtureId: number | null; // links the row to /match/{id}; falls back to the brief when absent
  dateLabel: string; // "Fri, 12 Jun" — server-formatted (timezone-anchored)
  briefDate: string; // "2026-06-12" for /brief/{date}
  group: string;
  home: string;
  away: string;
  homeScore: number;
  awayScore: number;
  winner: "home" | "away" | "draw";
}

/**
 * Flatten the standings snapshot's per-team recent_results into deduped,
 * group-tagged rows for the Latest Results widget, most-recent first. Each
 * finished match appears under both teams in the snapshot; we keep one row and
 * carry the group_name from its containing standings group.
 */
export function groupedResultRows(
  groups: GroupStandings[],
  limit = 8,
): ResultWidgetRow[] {
  const seen = new Set<string>();
  const rows: ResultWidgetRow[] = [];
  for (const g of groups) {
    for (const row of g.rows) {
      for (const r of row.recent_results ?? []) {
        if (
          r.home_team == null || r.away_team == null ||
          r.home_score == null || r.away_score == null
        ) {
          continue;
        }
        const key = `${r.kickoff_utc}-${r.home_team}-${r.away_team}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const hs = r.home_score;
        const as = r.away_score;
        rows.push({
          key,
          fixtureId: r.fixture_id ?? null,
          dateLabel: kickoffDayLabel(r.kickoff_utc),
          briefDate: dateKey(r.kickoff_utc),
          group: g.group_name,
          home: r.home_team,
          away: r.away_team,
          homeScore: hs,
          awayScore: as,
          winner: hs > as ? "home" : hs < as ? "away" : "draw",
        });
      }
    }
  }
  rows.sort((a, b) => b.key.localeCompare(a.key)); // key is kickoff-prefixed ISO
  return rows.slice(0, limit);
}
