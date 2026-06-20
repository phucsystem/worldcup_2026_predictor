const API_BASE = process.env.API_BASE ?? "http://localhost:8000";

export interface BriefSummary {
  date: string;
  title: string | null;
  summary: string | null;
}

export interface BriefDetail {
  date: string;
  title: string | null;
  summary: string | null;
  body_md: string | null;
  model_used: string | null;
  created_at: string | null;
}

export interface RecentResult {
  outcome: "W" | "D" | "L";
  home_team: string | null;
  away_team: string | null;
  home_score: number | null;
  away_score: number | null;
  kickoff_utc: string | null;
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
  stage: string | null;
  group_name: string | null;
  kickoff_utc: string | null;
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

export async function getKnockout(): Promise<KnockoutBracket> {
  return (await apiFetch<KnockoutBracket>("/api/fixtures/knockout")) ?? { rounds: [] };
}

export async function getStars(): Promise<StarRow[]> {
  return (await apiFetch<StarRow[]>("/api/stars")) ?? [];
}
