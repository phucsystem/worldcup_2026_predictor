// Pure helpers for the match analysis page. No React, no DOM, no fetch — so the
// state derivation, timeline running-score, scorer grouping and forecast hit/miss
// are unit-tested directly (lib/match.test.ts).
import type { MatchEvent } from "./api";

export type MatchStateName = "preview" | "live" | "finished";

// Keep these literals in sync with LIVE_STATUSES / FINISHED_STATUSES in
// backend app/api/fixtures.py (single tournament feed — duplication accepted
// over shared codegen).
const LIVE_STATUSES = new Set(["1H", "HT", "2H", "ET", "BT", "P", "LIVE"]);
const FINISHED_STATUSES = new Set(["FT", "AET", "PEN"]);

export function matchState(status: string | null): MatchStateName {
  const code = (status ?? "").trim().toUpperCase();
  if (LIVE_STATUSES.has(code)) return "live";
  if (FINISHED_STATUSES.has(code)) return "finished";
  return "preview";
}

export interface TimelineRow {
  minute: number;
  extra: number | null;
  type: string | null;
  detail: string | null;
  player: string | null;
  side: "home" | "away" | null;
  // Side credited with the goal (own goal credits the opponent) — null on
  // non-goal rows. Drives the running-score chip colour.
  scoringSide: "home" | "away" | null;
  // Running score after this event — only set on goal rows; null otherwise.
  score: { home: number; away: number } | null;
}

function isGoal(e: MatchEvent): boolean {
  return (e.type ?? "").toLowerCase() === "goal";
}

function isOwnGoal(e: MatchEvent): boolean {
  return (e.detail ?? "").toLowerCase() === "own goal";
}

function byMinute(a: MatchEvent, b: MatchEvent): number {
  if (a.minute !== b.minute) return a.minute - b.minute;
  return (a.extra ?? 0) - (b.extra ?? 0);
}

export function buildTimeline(events: MatchEvent[]): TimelineRow[] {
  const ordered = [...(events ?? [])].sort(byMinute);
  let home = 0;
  let away = 0;
  return ordered.map((e) => {
    let score: TimelineRow["score"] = null;
    let scoringSide: TimelineRow["scoringSide"] = null;
    if (isGoal(e)) {
      // An own goal credits the opposing side.
      scoringSide = isOwnGoal(e) ? (e.side === "home" ? "away" : "home") : e.side;
      if (scoringSide === "home") home += 1;
      else if (scoringSide === "away") away += 1;
      score = { home, away };
    }
    return {
      minute: e.minute,
      extra: e.extra,
      type: e.type,
      detail: e.detail,
      player: e.player,
      side: e.side,
      scoringSide,
      score,
    };
  });
}

export interface ScorerEntry {
  side: "home" | "away" | null;
  player: string | null;
  minutes: number[];
}

export function goalscorers(events: MatchEvent[]): ScorerEntry[] {
  const order: string[] = [];
  const byKey = new Map<string, ScorerEntry>();
  for (const e of (events ?? []).filter(isGoal)) {
    const key = `${e.side}|${e.player}`;
    let entry = byKey.get(key);
    if (!entry) {
      entry = { side: e.side, player: e.player, minutes: [] };
      byKey.set(key, entry);
      order.push(key);
    }
    entry.minutes.push(e.minute);
  }
  return order.map((k) => byKey.get(k)!);
}

export interface ForecastFactor {
  name: string;
  lean: "home" | "away" | "even";
  why: string;
}

export interface Forecast {
  homePct: number;
  drawPct: number;
  awayPct: number;
  factors: ForecastFactor[];
  note: string;
}

// The SINGLE source of the illustrative, non-data-driven forecast shown on the
// match page. Percentages and factor weightings are fixed placeholders to
// demonstrate the layout — never derived from data. The factor `why` copy is
// generic on purpose: inventing team-specific form/quality claims would be
// fabricated data, which the plan explicitly forbids.
export function placeholderForecast(home: string, away: string): Forecast {
  return {
    homePct: 64,
    drawPct: 22,
    awayPct: 14,
    factors: [
      {
        name: "Recent form",
        lean: "home",
        why: `Whichever of ${home} or ${away} enters on the stronger recent run is favoured to carry that momentum in.`,
      },
      {
        name: "Attacking quality",
        lean: "home",
        why: "Depth of game-changing forwards tilts the expected-goals edge toward the favourite.",
      },
      {
        name: "Head-to-head & ranking",
        lean: "even",
        why: `Historical meetings between ${home} and ${away} and the current ranking gap set the baseline expectation.`,
      },
      {
        name: "What's at stake",
        lean: "away",
        why: "A side that needs a result is likelier to press early — a route to an upset.",
      },
      {
        name: "Venue & rest",
        lean: "even",
        why: "A neutral venue and equal rest days leave little to separate the two.",
      },
    ],
    note: "Illustrative figures only — not produced by any model yet. A data-driven prediction engine is on the project roadmap; until it ships, these percentages and factor weightings are placeholders shown to demonstrate the forecast layout.",
  };
}

export type Side = "home" | "away" | "draw";

export interface ForecastOutcome {
  hit: boolean;
  predictedSide: Side;
  actualSide: Side;
}

export function forecastOutcome(
  forecast: Forecast,
  homeScore: number | null,
  awayScore: number | null,
): ForecastOutcome | null {
  if (homeScore == null || awayScore == null) return null;
  const predictedSide: Side =
    forecast.homePct >= forecast.drawPct && forecast.homePct >= forecast.awayPct
      ? "home"
      : forecast.awayPct >= forecast.drawPct
        ? "away"
        : "draw";
  const actualSide: Side =
    homeScore > awayScore ? "home" : homeScore < awayScore ? "away" : "draw";
  return { hit: predictedSide === actualSide, predictedSide, actualSide };
}
