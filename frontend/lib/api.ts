import type { Forecast } from "./match";

const API_BASE = process.env.API_BASE ?? "http://localhost:8000";

export interface BriefSummary {
  date: string;
  title: string | null;
  summary: string | null;
}

export interface FixtureStake {
  fixture_id: number;
  stake_text: string;
}

export interface ScenarioRow {
  position: number | null;
  team: string;
  points: number;
  note: string;
  status: "qualified" | "out" | "contention" | string;
}

export interface GroupScenario {
  group_name: string;
  tag: string;
  line: string;
  rows?: ScenarioRow[];
}

export interface Intelligence {
  storylines?: string[];
  surprise_teams?: string[];
  underperformers?: string[];
  power_ranking?: string[];
  qualification_narrative?: string;
  fixture_stakes?: FixtureStake[];
  group_scenarios?: GroupScenario[];
}

export interface BriefDetail {
  date: string;
  title: string | null;
  summary: string | null;
  body_md: string | null;
  model_used: string | null;
  created_at: string | null;
  intelligence?: Intelligence | null;
}

export interface TournamentSummary {
  stage: string;
  matchday: number;
  matchday_total: number;
  teams_remaining: number;
  teams_total: number;
  days_to_next_phase: number | null;
  next_phase_label: string | null;
  group_stage_pct: number;
}

export interface RecentResult {
  outcome: "W" | "D" | "L";
  fixture_id: number | null;
  home_team: string | null;
  away_team: string | null;
  home_score: number | null;
  away_score: number | null;
  kickoff_utc: string | null;
  // Whether the pre-match forecast called the right side; null when the match
  // carried no forecast (forecast scope is group-stage only).
  forecast_correct?: boolean | null;
}

export interface StandingRow {
  position: number | null;
  prev_position: number | null;
  team: string | null;
  played: number | null;
  won: number | null;
  drawn: number | null;
  lost: number | null;
  gf: number | null;
  ga: number | null;
  gd: number | null;
  points: number | null;
  qualification: string | null;
  logo?: string | null;
  recent_results?: RecentResult[];
}

export interface FixtureRow {
  fixture_id: number;
  home_team: string | null;
  away_team: string | null;
  home_logo: string | null;
  away_logo: string | null;
  home_score: number | null;
  away_score: number | null;
  status: string | null;
  elapsed: number | null;
  stage: string | null;
  group_name: string | null;
  kickoff_utc: string | null;
  updated_at: string | null;
}

// Mirrors backend app.api.fixtures.MatchEvent (normalize_events output).
export interface MatchEvent {
  minute: number;
  extra: number | null;
  type: string | null;
  detail: string | null;
  player: string | null;
  assist: string | null;
  team: string | null;
  side: "home" | "away" | null;
}

// Mirrors backend app.api.fixtures.MatchStat (normalize_statistics output).
export interface MatchStat {
  label: string;
  home: string;
  away: string;
  home_pct: number;
  away_pct: number;
}

export interface FixtureDetail extends FixtureRow {
  events: MatchEvent[];
  statistics: MatchStat[];
  verdict: string | null;
  verdict_model: string | null;
  forecast: Forecast | null;
}

export interface FixtureDay {
  date: string;
  fixtures: FixtureRow[];
}

export interface UpcomingFixtures {
  up_next: FixtureRow | null;
  days: FixtureDay[];
}

export interface KnockoutRound {
  round: string;
  ties: FixtureRow[];
}

export interface KnockoutBracket {
  rounds: KnockoutRound[];
}

export interface StarRow {
  player_id: number;
  name: string;
  team: string | null;
  goals: number;
  photo_url: string | null;
}

export interface GroupStandings {
  group_name: string;
  rows: StandingRow[];
}

export interface StandingsSnapshot {
  snapshot_date: string | null;
  groups: GroupStandings[];
}

export interface LogEvent {
  id: number;
  ts: string;
  level: string;
  source: string;
  message: string;
  context: Record<string, unknown> | null;
  run_id: string | null;
}

export interface LogPage {
  items: LogEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface LogQuery {
  level?: string;
  q?: string;
  source?: string;
  limit?: number;
  offset?: number;
}

const NO_STORE = { cache: "no-store" } as const;

async function apiFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, NO_STORE);
    if (!res.ok) return null;
    return res.json() as Promise<T>;
  } catch {
    return null;
  }
}

export async function listBriefs(): Promise<BriefSummary[]> {
  return (await apiFetch<BriefSummary[]>("/api/briefs")) ?? [];
}

export async function getLatestBrief(): Promise<BriefDetail | null> {
  return apiFetch<BriefDetail>("/api/briefs/latest");
}

export async function getBrief(date: string): Promise<BriefDetail | null> {
  return apiFetch<BriefDetail>(`/api/briefs/${date}`);
}

export async function getStandings(date?: string): Promise<StandingsSnapshot | null> {
  const qs = date ? `?date=${date}` : "";
  return apiFetch<StandingsSnapshot>(`/api/standings${qs}`);
}

export async function getUpcomingFixtures(): Promise<UpcomingFixtures> {
  return (
    (await apiFetch<UpcomingFixtures>("/api/fixtures/upcoming")) ?? {
      up_next: null,
      days: [],
    }
  );
}

export async function getLiveFixtures(): Promise<FixtureRow[]> {
  return (await apiFetch<FixtureRow[]>("/api/fixtures/live")) ?? [];
}

export async function getFixture(fixtureId: number): Promise<FixtureDetail | null> {
  return apiFetch<FixtureDetail>(`/api/fixtures/${fixtureId}`);
}

export async function getKnockout(): Promise<KnockoutBracket> {
  return (await apiFetch<KnockoutBracket>("/api/fixtures/knockout")) ?? { rounds: [] };
}

export async function getStars(): Promise<StarRow[]> {
  return (await apiFetch<StarRow[]>("/api/stars")) ?? [];
}

export async function getTournamentSummary(): Promise<TournamentSummary | null> {
  return apiFetch<TournamentSummary>("/api/tournament/summary");
}

// ---- Feedback ----
export type FeedbackTopic = "bug" | "feature" | "other";
export type FeedbackStatus = "new" | "done" | "wont";

export interface Feedback {
  id: number;
  created_at: string;
  message: string;
  topic: FeedbackTopic | null;
  page: string | null;
  status: FeedbackStatus;
  resolved_at: string | null;
}

// Server-to-server (called from Next route handlers); the backend stays GET-only
// for the browser. Returns true on success so the widget can show its thank-you.
export async function submitFeedback(input: {
  message: string;
  topic?: string | null;
  page?: string | null;
}): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
      cache: "no-store",
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function listFeedback(status?: FeedbackStatus): Promise<Feedback[]> {
  const qs = status ? `?status=${status}` : "";
  return (await apiFetch<Feedback[]>(`/api/feedback${qs}`)) ?? [];
}

export async function updateFeedbackStatus(
  id: number,
  status: FeedbackStatus,
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/feedback/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
      cache: "no-store",
    });
    return res.ok;
  } catch {
    return false;
  }
}

// Unlike the other helpers, this throws on upstream failure so the same-origin
// proxy can return a non-200 and the console's error state can engage (rather
// than silently rendering an empty page).
export async function getLogs(params: LogQuery = {}): Promise<LogPage> {
  const qs = new URLSearchParams();
  if (params.level) qs.set("level", params.level);
  if (params.q) qs.set("q", params.q);
  if (params.source) qs.set("source", params.source);
  if (params.limit != null) qs.set("limit", String(params.limit));
  if (params.offset != null) qs.set("offset", String(params.offset));
  const query = qs.toString();
  const res = await fetch(`${API_BASE}/api/logs${query ? `?${query}` : ""}`, NO_STORE);
  if (!res.ok) throw new Error(`logs upstream ${res.status}`);
  return res.json() as Promise<LogPage>;
}
