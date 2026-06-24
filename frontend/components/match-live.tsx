"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import type { FixtureDetail } from "@/lib/api";
import TeamFlag from "@/components/team-flag";
import MatchTimeline from "@/components/match-timeline";
import Goalscorers from "@/components/goalscorers";
import MatchScorersStrip from "@/components/match-scorers-strip";
import MatchStats from "@/components/match-stats";
import FlagBackdrop from "@/components/flag-backdrop";
import ShareResultButton from "@/components/share-result-button";
import { liveMinute } from "@/lib/live";
import { eventKey, freshEventKeys, sbsSearchUrl } from "@/lib/match";

interface Props {
  initial: FixtureDetail;
  forecastSlot: ReactNode;
  formSlot: ReactNode;
  stakesSlot: ReactNode;
  teamStatusSlot: ReactNode;
}

const POLL_MS = 30_000;
const TICK_MS = 1_000;
const SHORT_FROZEN: Record<string, string> = { HT: "HT", BT: "BREAK", P: "PENS" };

export default function MatchLive({ initial, forecastSlot, formSlot, stakesSlot, teamStatusSlot }: Props) {
  const [fixture, setFixture] = useState<FixtureDetail>(initial);
  const [nowMs, setNowMs] = useState<number>(() => {
    const t = initial.updated_at ? Date.parse(initial.updated_at) : NaN;
    return Number.isNaN(t) ? 0 : t;
  });
  const [freshKeys, setFreshKeys] = useState<Set<string>>(() => new Set());
  const inFlight = useRef(false);
  // Seeded from the initial SSR payload so the first paint highlights nothing —
  // only events that appear on a later poll are "fresh".
  const seenKeys = useRef<Set<string>>(new Set(initial.events.map(eventKey)));

  useEffect(() => {
    const tick = setInterval(() => setNowMs(Date.now()), TICK_MS);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    async function poll() {
      if (inFlight.current) return;
      inFlight.current = true;
      try {
        const res = await fetch(`/api/fixtures/${initial.fixture_id}`, { cache: "no-store" });
        if (!res.ok) return;
        const next: FixtureDetail = await res.json();
        const fresh = freshEventKeys(seenKeys.current, next.events);
        next.events.forEach((e) => seenKeys.current.add(eventKey(e)));
        setFixture(next);
        if (fresh.length > 0) setFreshKeys(new Set(fresh));
      } catch {
        // keep the last good state on a transient failure
      } finally {
        inFlight.current = false;
      }
    }
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, [initial.fixture_id]);

  const { minute, frozen, label } = liveMinute(
    fixture.elapsed,
    fixture.updated_at,
    fixture.status,
    nowMs,
  );
  const code = (fixture.status ?? "").toUpperCase();
  const clock = frozen ? (SHORT_FROZEN[code] ?? label) : minute != null ? `${minute}'` : "LIVE";

  const sbsUrl = sbsSearchUrl(fixture.home_team, fixture.away_team);

  return (
    <>
      <section
        className="next-match is-live"
        data-flag-bg
        aria-label={`Live now: ${fixture.home_team ?? "TBD"} ${fixture.home_score ?? 0}, ${fixture.away_team ?? "TBD"} ${fixture.away_score ?? 0}, ${label}`}
      >
        <FlagBackdrop home={fixture.home_team} away={fixture.away_team} />
        <span className="nm-eyebrow">
          <span className="dot" /> Live now · {label}
        </span>
        <div className="nm-body">
          <span className="nm-side">
            <TeamFlag team={fixture.home_team} logo={fixture.home_logo} size={40} />
            {fixture.home_team ?? "TBD"}
          </span>
          <span className="nm-score" aria-hidden="true">
            <span className="nm-sc">{fixture.home_score ?? 0}</span>
            <span className="nm-sc-sep">–</span>
            <span className="nm-sc">{fixture.away_score ?? 0}</span>
          </span>
          <span className="nm-side">
            {fixture.away_team ?? "TBD"}
            <TeamFlag team={fixture.away_team} logo={fixture.away_logo} size={40} />
          </span>
        </div>
        <MatchScorersStrip events={fixture.events} />
        <div className="nm-meta">{fixture.group_name ?? "Live"}</div>
        <div className="nm-live-clock-wrap">
          <span className="nm-live-clock" aria-hidden="true">
            {clock}
          </span>
        </div>
        <div className="nm-actions">
          <a
            className="nm-watch"
            href={sbsUrl}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Find ${fixture.home_team ?? "this match"} v ${fixture.away_team ?? ""} on SBS On Demand (opens in a new tab)`}
          >
            <span className="nw-dot" aria-hidden="true" /> Watch live on SBS
          </a>
          <ShareResultButton
            fixtureId={fixture.fixture_id}
            label="Share live score"
            shareTitle={`${fixture.home_team ?? "TBD"} ${fixture.home_score ?? 0}–${fixture.away_score ?? 0} ${fixture.away_team ?? "TBD"}`}
          />
        </div>
      </section>

      {forecastSlot}

      {fixture.events.length > 0 ? (
        <>
          <h2 className="section-title">Key moments</h2>
          <MatchTimeline events={fixture.events} homeTeam={fixture.home_team} awayTeam={fixture.away_team} freshKeys={freshKeys} />
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

      {formSlot}
      {teamStatusSlot}
      {stakesSlot}
    </>
  );
}
