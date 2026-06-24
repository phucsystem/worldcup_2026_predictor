"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import type { FixtureDetail } from "@/lib/api";
import MatchTimeline from "@/components/match-timeline";
import Goalscorers from "@/components/goalscorers";
import MatchStats from "@/components/match-stats";
import MatchBanner from "@/components/match-banner";
import { liveMinute } from "@/lib/live";
import { eventKey, freshEventKeys } from "@/lib/match";

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

  return (
    <>
      <section
        className="next-match is-live"
        data-flag-bg
        aria-label={`Live now: ${fixture.home_team ?? "TBD"} ${fixture.home_score ?? 0}, ${fixture.away_team ?? "TBD"} ${fixture.away_score ?? 0}, ${label}`}
      >
        <MatchBanner
          fixture={fixture}
          variant="live"
          eyebrowLabel={`Live now · ${label}`}
          events={fixture.events}
          meta={fixture.group_name ?? fixture.stage ?? null}
          belowMeta={
            <div className="nm-live-clock-wrap">
              <span className="nm-live-clock" aria-hidden="true">{clock}</span>
            </div>
          }
          watchLabel="Watch live on SBS"
          watchLive
          shareLabel="Share live score"
          shareTitle={`${fixture.home_team ?? "TBD"} ${fixture.home_score ?? 0}–${fixture.away_score ?? 0} ${fixture.away_team ?? "TBD"}`}
        />
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
