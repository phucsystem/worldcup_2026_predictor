import Link from "next/link";
import {
  listBriefs,
  getLatestBrief,
  getUpcomingFixtures,
  getLiveFixtures,
  getStars,
  getStandings,
  getTournamentSummary,
} from "@/lib/api";
import type { FixtureRow as Fixture, RecentResult } from "@/lib/api";
import { HeroBriefCard, CompactBriefCard } from "@/components/brief-card";
import StarCard from "@/components/star-card";
import ResultChips from "@/components/result-chip";
import EmptyState from "@/components/empty-state";
import SummaryPanel from "@/components/summary-panel";
import NextMatchCard from "@/components/next-match-card";
import LiveMatchCard from "@/components/live-match-card";
import ResultsWidget from "@/components/results-widget";
import StakeGrid from "@/components/stake-grid";
import { groupedResultRows } from "@/lib/results";
import { scenariosForDisplay, stakesByFixtureId } from "@/lib/stakes";
import TeamFlag from "@/components/team-flag";
import LocalTime from "@/components/local-time";

export const dynamic = "force-dynamic";

// The "Today" heading is the editorial brief day, which is anchored to the
// publishing timezone (not the viewer's). Computed per request so a
// long-running server never serves a stale date.
function todayLabel(): string {
  return (
    "Today · " +
    new Date().toLocaleDateString("en-AU", {
      timeZone: "Australia/Melbourne",
      day: "numeric",
      month: "short",
      year: "numeric",
    })
  );
}

// Collect the most-recent unique finished matches from the standings payload
// (each match appears under both teams). Outcome is normalised to the home
// team's perspective so the chip strip reads neutrally.
function recentResultStrip(
  groups: { rows: { recent_results?: RecentResult[] }[] }[],
  limit = 6,
): RecentResult[] {
  const seen = new Set<string>();
  const matches: RecentResult[] = [];
  for (const g of groups) {
    for (const row of g.rows) {
      for (const r of row.recent_results ?? []) {
        const key = `${r.kickoff_utc}-${r.home_team}-${r.away_team}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const hs = r.home_score ?? 0;
        const as = r.away_score ?? 0;
        matches.push({ ...r, outcome: hs > as ? "W" : hs === as ? "D" : "L" });
      }
    }
  }
  // kickoff_utc is ISO-8601 UTC from the API, so string compare = chronological.
  matches.sort((a, b) => (b.kickoff_utc ?? "").localeCompare(a.kickoff_utc ?? ""));
  return matches.slice(0, limit);
}

const STAKES_SECTION_TITLE = "What's at stake";
const STAKES_SECTION_DECK =
  "Who can clinch, who needs a result, and which groups can still turn on the next match.";

function CompactFixtureStrip({ fixtures }: { fixtures: Fixture[] }) {
  if (fixtures.length === 0) return null;

  return (
    <div className="next-two" aria-label="Next two fixtures">
      <span className="next-two-label">Next 2</span>
      {fixtures.map((fixture) => (
        <Link
          key={fixture.fixture_id}
          className="next-two-match"
          href={`/match/${fixture.fixture_id}`}
        >
          <span className="next-two-time">
            <LocalTime iso={fixture.kickoff_utc} mode="time" withZone />{" "}
            <LocalTime iso={fixture.kickoff_utc} mode="day" />
          </span>
          <span className="next-two-teams">
            <TeamFlag team={fixture.home_team} logo={fixture.home_logo} size={18} />
            {fixture.home_team ?? "TBD"} vs {fixture.away_team ?? "TBD"}
            <TeamFlag team={fixture.away_team} logo={fixture.away_logo} size={18} />
          </span>
          {fixture.group_name && <span className="group-pill">{fixture.group_name}</span>}
        </Link>
      ))}
      <Link className="next-two-all" href="/fixtures">
        All fixtures →
      </Link>
    </div>
  );
}

export default async function HomePage() {
  const [latest, briefs, upcoming, live, stars, standings, summary] = await Promise.all([
    getLatestBrief(),
    listBriefs(),
    getUpcomingFixtures(),
    getLiveFixtures(),
    getStars(),
    getStandings(),
    getTournamentSummary(),
  ]);

  const earlier = briefs.filter((b) => b.date !== latest?.date).slice(0, 9);
  // A live match takes the lead card; the soonest in-play game (API returns
  // them soonest-kicked first). Falls back to the next upcoming match.
  const liveMatch = live[0] ?? null;
  const upNext = upcoming.up_next;
  const topStars = stars.slice(0, 6);
  const recentResults = recentResultStrip(standings?.groups ?? []);
  const widgetRows = groupedResultRows(standings?.groups ?? [], 8);

  const stakeMap = stakesByFixtureId(latest?.intelligence);
  const scenarios = scenariosForDisplay(latest?.intelligence);

  // Next two fixtures after the featured up-next (flatten upcoming days).
  const nextFixtures: Fixture[] = upcoming.days
    .flatMap((d) => d.fixtures)
    .filter((f) => f.fixture_id !== upNext?.fixture_id)
    .slice(0, 2);

  return (
    <div className="home-shell">
      <main className="main-content reading analysis" data-cjx-entrance>
      <h1 className="sr-only">WC26 Intelligence — Daily Brief</h1>

      <SummaryPanel summary={summary} dateLabel={todayLabel()} freshLabel="Updated hourly" />

      {(liveMatch || upNext || nextFixtures.length > 0) && (
        <section aria-label={liveMatch ? "Live now" : "Up next"}>
          <h2 className="section-title">{liveMatch ? "Live now" : "Up next"}</h2>
          {liveMatch ? (
            <LiveMatchCard initial={liveMatch} />
          ) : (
            upNext && (
              <NextMatchCard fixture={upNext} stakeText={stakeMap.get(upNext.fixture_id)} />
            )
          )}
          <CompactFixtureStrip fixtures={nextFixtures} />
        </section>
      )}

      {widgetRows.length > 0 && <ResultsWidget rows={widgetRows} viewAllHref="/results" />}

      {latest ? (
        <section aria-label="Today's brief">
          <h2 className="section-title">Today&apos;s brief</h2>
          <HeroBriefCard brief={latest} />
          {recentResults.length > 0 && (
            <div className="mt-4">
              <ResultChips results={recentResults} />
            </div>
          )}
        </section>
      ) : (
        <section aria-label="Today's brief">
          <h2 className="section-title">Today&apos;s brief</h2>
          <EmptyState
            message="Latest intelligence is not published yet"
            subtext="The collector and analysis pipeline refreshes hourly."
          />
        </section>
      )}

      {scenarios.length > 0 && (
        <section aria-label={STAKES_SECTION_TITLE}>
          <h2 className="section-title">{STAKES_SECTION_TITLE}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[color:var(--text-secondary)]">
            {STAKES_SECTION_DECK}
          </p>
          <StakeGrid scenarios={scenarios} />
        </section>
      )}

      {topStars.length > 0 && (
        <section aria-label="Stars to watch">
          <h2 className="section-title">Stars to watch</h2>
          <div className="flex gap-3 overflow-x-auto pb-2" style={{ WebkitOverflowScrolling: "touch" }}>
            {topStars.map((s) => (
              <StarCard key={s.player_id} player={s} />
            ))}
          </div>
        </section>
      )}

      {earlier.length > 0 && (
        <section aria-label="Earlier briefs">
          <h2 className="section-title">Earlier</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {earlier.map((b) => (
              <CompactBriefCard key={b.date} brief={b} />
            ))}
          </div>
          <div className="mt-6 text-center">
            <Link
              href="/archive"
              className="text-sm font-medium hover:underline"
              style={{ color: "#2D6BF6" }}
            >
              View archive →
            </Link>
          </div>
        </section>
      )}
      </main>
    </div>
  );
}
