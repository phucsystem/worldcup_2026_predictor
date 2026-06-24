// Pure data→view helper mapping recent finished matches into ResultChip props.
import type { GroupStandings, RecentResult, ResultItem } from "@/lib/api";
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
  forecastCorrect: boolean | null; // null when the match carried no forecast
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
          forecastCorrect: r.forecast_correct ?? null,
        });
      }
    }
  }
  rows.sort((a, b) => b.key.localeCompare(a.key)); // key is kickoff-prefixed ISO
  return rows.slice(0, limit);
}

/**
 * Map the full `/api/results` list into ResultWidgetRow[] for the all-results
 * page. Unlike groupedResultRows this has no per-team 5-cap and no limit — every
 * finished match from the start of the tournament. Group-stage matches show their
 * group letter; knockout matches fall back to their round (`stage`).
 */
export function resultRowsFromResults(items: ResultItem[]): ResultWidgetRow[] {
  const rows: ResultWidgetRow[] = [];
  for (const item of items) {
    if (
      item.home_team == null || item.away_team == null ||
      item.home_score == null || item.away_score == null
    ) {
      continue;
    }
    const hs = item.home_score;
    const as = item.away_score;
    rows.push({
      key: `${item.kickoff_utc}-${item.home_team}-${item.away_team}`,
      fixtureId: item.fixture_id ?? null,
      dateLabel: kickoffDayLabel(item.kickoff_utc),
      briefDate: dateKey(item.kickoff_utc),
      group: item.group_name ?? item.stage ?? "—",
      home: item.home_team,
      away: item.away_team,
      homeScore: hs,
      awayScore: as,
      winner: hs > as ? "home" : hs < as ? "away" : "draw",
      forecastCorrect: item.forecast_correct ?? null,
    });
  }
  rows.sort((a, b) => b.key.localeCompare(a.key)); // key is kickoff-prefixed ISO
  return rows;
}
