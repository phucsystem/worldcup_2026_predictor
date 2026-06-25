import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { getFixture, getStandings } from "@/lib/api";
import { matchState } from "@/lib/match";
import NextMatchCard from "@/components/next-match-card";
import MatchHeroFinal from "@/components/match-hero-final";
import MatchTimeline from "@/components/match-timeline";
import Goalscorers from "@/components/goalscorers";
import MatchStats from "@/components/match-stats";
import FormCompare from "@/components/form-compare";
import QualificationStakes from "@/components/qualification-stakes";
import TeamStatusSection from "@/components/team-status";
import ForecastCard from "@/components/forecast-card";
import ForecastOutcome from "@/components/forecast-outcome";
import MatchLive from "@/components/match-live";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ fixture_id: string }>;
}): Promise<Metadata> {
  const { fixture_id } = await params;
  const fixture = await getFixture(Number(fixture_id));
  if (!fixture) return {};
  const home = fixture.home_team ?? "TBD";
  const away = fixture.away_team ?? "TBD";
  const scored =
    fixture.home_score != null && fixture.away_score != null
      ? `${home} ${fixture.home_score}–${fixture.away_score} ${away}`
      : `${home} vs ${away}`;
  const state = matchState(fixture.status);
  const title =
    state === "live" ? `LIVE: ${scored}` : state === "finished" ? `${scored} · Full Time` : scored;
  const description = `${scored}${fixture.group_name ? ` · ${fixture.group_name}` : ""} — World Cup 2026 result, forecast and analysis.`;
  return {
    title,
    description,
    openGraph: { title, description, type: "website" },
    twitter: { card: "summary_large_image", title, description },
  };
}

export default async function MatchPage({ params }: { params: Promise<{ fixture_id: string }> }) {
  const { fixture_id } = await params;
  const id = Number(fixture_id);
  if (!Number.isFinite(id)) notFound();

  const [fixture, standings] = await Promise.all([getFixture(id), getStandings()]);
  if (!fixture) notFound();

  const state = matchState(fixture.status);
  const homeTeam = fixture.home_team ?? "Home";
  const awayTeam = fixture.away_team ?? "Away";
  const forecast = fixture.forecast;

  const group = standings?.groups.find((g) => g.group_name === fixture.group_name) ?? null;
  const groupRows = group?.rows ?? [];
  const homeRow = groupRows.find((r) => r.team === fixture.home_team);
  const awayRow = groupRows.find((r) => r.team === fixture.away_team);

  const updatedAt = fixture.updated_at
    ? new Date(fixture.updated_at).toLocaleString("en-AU", {
        timeZone: "Australia/Melbourne",
        dateStyle: "medium",
        timeStyle: "short",
      })
    : null;

  const forecastCard = forecast ? (
    <ForecastCard forecast={forecast} homeTeam={homeTeam} awayTeam={awayTeam} />
  ) : null;
  const formCompare = (
    <FormCompare
      home={{ team: fixture.home_team, logo: homeRow?.logo ?? fixture.home_logo, results: homeRow?.recent_results ?? [] }}
      away={{ team: fixture.away_team, logo: awayRow?.logo ?? fixture.away_logo, results: awayRow?.recent_results ?? [] }}
    />
  );
  const stakes = <QualificationStakes groupName={fixture.group_name} rows={groupRows} state={state} />;
  const teamStatus = (
    <TeamStatusSection
      home={{ team: fixture.home_team, logo: homeRow?.logo ?? fixture.home_logo, status: fixture.home_status }}
      away={{ team: fixture.away_team, logo: awayRow?.logo ?? fixture.away_logo, status: fixture.away_status }}
    />
  );

  return (
    <div className="px-6 py-8" style={{ maxWidth: "960px", margin: "0 auto" }}>
      <nav aria-label="Breadcrumb">
        <Link
          href="/"
          className="text-sm mb-6 inline-block hover:text-white transition-colors focus-visible:rounded"
          style={{ color: "#6B7A9E" }}
        >
          ← Back to Today
        </Link>
      </nav>

      <div className="flex flex-col" style={{ gap: "var(--space-6)" }}>
        {state === "live" ? (
          <MatchLive
            initial={fixture}
            formSlot={formCompare}
            stakesSlot={stakes}
            teamStatusSlot={teamStatus}
          />
        ) : state === "finished" ? (
          <>
            <MatchHeroFinal fixture={fixture} />
            {fixture.verdict ? (
              <div className="analysis-note">
                <span className="an-eyebrow">The verdict</span>
                <p>{fixture.verdict}</p>
              </div>
            ) : null}
            {forecastCard}
            {forecast ? (
              <ForecastOutcome
                forecast={forecast}
                homeTeam={fixture.home_team}
                awayTeam={fixture.away_team}
                homeLogo={fixture.home_logo}
                awayLogo={fixture.away_logo}
                homeScore={fixture.home_score}
                awayScore={fixture.away_score}
              />
            ) : null}
            {fixture.events.length > 0 ? (
              <>
                <h2 className="section-title">Key moments</h2>
                <MatchTimeline events={fixture.events} homeTeam={fixture.home_team} awayTeam={fixture.away_team} />
                <h2 className="section-title">Goalscorers</h2>
                <Goalscorers
                  events={fixture.events}
                  homeTeam={fixture.home_team}
                  awayTeam={fixture.away_team}
                  homeLogo={fixture.home_logo}
                  awayLogo={fixture.away_logo}
                />
              </>
            ) : null}
            {fixture.statistics.length > 0 ? (
              <>
                <h2 className="section-title">Match stats</h2>
                <MatchStats stats={fixture.statistics} homeTeam={fixture.home_team} awayTeam={fixture.away_team} />
              </>
            ) : null}
            {stakes}
          </>
        ) : (
          <>
            <NextMatchCard fixture={fixture} forecast={fixture.forecast} linked={false} />
            {forecastCard}
            {formCompare}
            {teamStatus}
            {stakes}
          </>
        )}

        <footer style={{ marginTop: "var(--space-4)" }}>
          <Link
            href="/"
            className="inline-block text-sm mb-4 hover:text-white transition-colors"
            style={{ color: "var(--accent-bright)" }}
          >
            Read the full brief →
          </Link>
          <p className="provenance">
            <span>Data: API-Football</span>
            {fixture.verdict_model ? <span>· verdict: {fixture.verdict_model}</span> : null}
            {forecast?.model ? <span>· forecast: {forecast.model}</span> : null}
            {state === "live" && fixture.live_winprob ? (
              <span>· live win prob: Python base + AI adjustment (bounded)</span>
            ) : null}
            {state === "live" && fixture.live_read_model ? (
              <span>· live read: {fixture.live_read_model}</span>
            ) : null}
            {updatedAt ? <span>· Updated {updatedAt} AEST</span> : null}
          </p>
        </footer>
      </div>
    </div>
  );
}
