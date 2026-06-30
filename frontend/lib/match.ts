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

export function matchState(status: string | null | undefined): MatchStateName {
  const code = (status ?? "").trim().toUpperCase();
  if (LIVE_STATUSES.has(code)) return "live";
  if (FINISHED_STATUSES.has(code)) return "finished";
  return "preview";
}

// Decided side of a finished match. Prefers winner_side (set on the advancing
// side for knockout ties decided in extra time or on penalties — even when the
// regulation score is level), else the regulation score. Returns null while
// unfinished; "draw" only for a level regulation result with no winner_side.
export function resolveWinner(m: {
  status?: string | null;
  home_score: number | null;
  away_score: number | null;
  winner_side?: "home" | "away" | null;
}): "home" | "away" | "draw" | null {
  if (matchState(m.status) !== "finished") return null;
  if (m.winner_side === "home" || m.winner_side === "away") return m.winner_side;
  if (m.home_score == null || m.away_score == null) return null;
  if (m.home_score > m.away_score) return "home";
  if (m.away_score > m.home_score) return "away";
  return "draw";
}

// Friendly label for how a finished match ended: knockout ties decided later
// read "After Extra Time" / "Penalties"; everything else "Full Time".
export function finishedStatusLabel(status: string | null | undefined): string {
  const code = (status ?? "").trim().toUpperCase();
  if (code === "PEN") return "Penalties";
  if (code === "AET") return "After Extra Time";
  return "Full Time";
}

// A match plausibly still in play: kickoff has passed but not by more than a full
// match's worth of time (90' + ET + penalties + stoppage, generously 4h). Bounds
// the live fallback so a fixture left at NS for days (stale/postponed data, or an
// old seeded fixture) is NOT treated as live — only a genuinely just-started one.
const LIVE_FALLBACK_WINDOW_MS = 4 * 60 * 60 * 1000;

export function isRecentlyKickedOff(kickoffUtc: string | null): boolean {
  if (!kickoffUtc) return false;
  const t = Date.parse(kickoffUtc);
  if (!Number.isFinite(t)) return false;
  const now = Date.now();
  return t <= now && now - t <= LIVE_FALLBACK_WINDOW_MS;
}

// Like matchState but treats a just-kicked-off NS match (poller lag) as "live".
export function effectiveMatchState(status: string | null, kickoffUtc: string | null): MatchStateName {
  const state = matchState(status);
  if (state === "preview" && isRecentlyKickedOff(kickoffUtc)) return "live";
  return state;
}

export interface TimelineRow {
  minute: number;
  extra: number | null;
  type: string | null;
  detail: string | null;
  player: string | null;
  assist: string | null;
  team: string | null;
  side: "home" | "away" | null;
  // Side credited with the goal — null on non-goal rows. Drives the
  // running-score chip colour. Equals the event's own side: the data records an
  // own goal under the team it benefits, so there is no opponent-flip here.
  scoringSide: "home" | "away" | null;
  // Running score after this event — only set on goal rows; null otherwise.
  score: { home: number; away: number } | null;
}

function isGoal(e: MatchEvent): boolean {
  if ((e.type ?? "").toLowerCase() !== "goal") return false;
  // API-Football logs a missed/saved penalty as a "Goal"-type event with
  // detail "Missed Penalty" — it never changes the score, so it is not a goal.
  return (e.detail ?? "").toLowerCase() !== "missed penalty";
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
      // The event's `side` is already the team credited with the goal. Own goals
      // are recorded under the team they benefit (not the conceding side), so the
      // running score follows `side` directly — same as goalscorers().
      scoringSide = e.side;
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
      assist: e.assist,
      team: e.team,
      side: e.side,
      scoringSide,
      score,
    };
  });
}

// API-Football `subst` events carry the player coming ON in `player` and the
// player going OFF in `assist`. This is the documented convention; the live DB
// was unavailable to verify against a real payload when this was written.
export function subOnOff(e: Pick<MatchEvent, "player" | "assist">): {
  on: string | null;
  off: string | null;
} {
  return { on: e.player, off: e.assist };
}

// MatchEvent has no stable id, so identity is a composite of the fields that
// uniquely place an event in the match. Used to detect events newly arrived on
// a live poll (Phase E highlight).
type EventIdentity = Pick<
  MatchEvent,
  "minute" | "extra" | "type" | "detail" | "player" | "team" | "side"
>;

export function eventKey(e: EventIdentity): string {
  // `detail` and `team` are included so player-less events (VAR rulings, subs
  // with a missing name) at the same minute don't collide and miss a highlight.
  return [e.minute, e.extra ?? "", e.type ?? "", e.detail ?? "", e.player ?? "", e.team ?? "", e.side ?? ""].join("|");
}

// Keys present in `events` but not in `prevKeys` — i.e. events that appeared
// since the previous poll. Order follows `events`.
export function freshEventKeys(prevKeys: Set<string>, events: MatchEvent[]): string[] {
  return (events ?? []).map(eventKey).filter((k) => !prevKeys.has(k));
}

export interface ScorerGoal {
  minute: number;
  detail: string | null;
  assist: string | null;
}

export interface ScorerEntry {
  side: "home" | "away" | null;
  player: string | null;
  minutes: number[];
  goals: ScorerGoal[];
}

// SBS On Demand has no public fixture→video-ID mapping, so deep-link to its
// search (path-segment form) pre-filled with both team names; falls back to the
// football hub when a team is unknown. Shared by the live and finished heroes.
export function sbsSearchUrl(home: string | null, away: string | null): string {
  return home && away
    ? `https://www.sbs.com.au/ondemand/search/${encodeURIComponent(`${home} ${away}`)}`
    : "https://www.sbs.com.au/sport/football";
}

export function goalscorers(events: MatchEvent[]): ScorerEntry[] {
  const order: string[] = [];
  const byKey = new Map<string, ScorerEntry>();
  for (const e of (events ?? []).filter(isGoal)) {
    const key = `${e.side}|${e.player}`;
    let entry = byKey.get(key);
    if (!entry) {
      entry = { side: e.side, player: e.player, minutes: [], goals: [] };
      byKey.set(key, entry);
      order.push(key);
    }
    entry.minutes.push(e.minute);
    entry.goals.push({ minute: e.minute, detail: e.detail, assist: e.assist });
  }
  return order.map((k) => byKey.get(k)!);
}

export interface ForecastFactor {
  name: string;
  lean: "home" | "away" | "even";
  why: string;
}

// Mirrors backend app.api.fixtures.MatchForecast — a model-generated pre-kickoff
// win/draw/win split (sums to 100) plus the factors driving it. `model` names the
// producing model. Populated by the forecast pipeline; absent until it has run.
export interface Forecast {
  home_pct: number;
  draw_pct: number;
  away_pct: number;
  factors: ForecastFactor[];
  model?: string | null;
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
    forecast.home_pct >= forecast.draw_pct && forecast.home_pct >= forecast.away_pct
      ? "home"
      : forecast.away_pct >= forecast.draw_pct
        ? "away"
        : "draw";
  const actualSide: Side =
    homeScore > awayScore ? "home" : homeScore < awayScore ? "away" : "draw";
  return { hit: predictedSide === actualSide, predictedSide, actualSide };
}
