"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import type { FixtureDetail } from "@/lib/api";
import MatchTimeline from "@/components/match-timeline";
import Goalscorers from "@/components/goalscorers";
import MatchStats from "@/components/match-stats";
import MatchBanner from "@/components/match-banner";
import LiveWinProb from "@/components/live-winprob";
import LiveWinProbChart from "@/components/live-winprob-chart";
import { liveMinute } from "@/lib/live";
import { eventKey, freshEventKeys } from "@/lib/match";

interface Props {
  initial: FixtureDetail;
  formSlot: ReactNode;
  stakesSlot: ReactNode;
  teamStatusSlot: ReactNode;
}

function countReds(events: FixtureDetail["events"]): number {
  return events.filter(
    (e) => (e.type ?? "").toLowerCase() === "card" && (e.detail ?? "").toLowerCase().includes("red"),
  ).length;
}

const POLL_MS = 30_000;
const TICK_MS = 1_000;
const SHORT_FROZEN: Record<string, string> = { HT: "HT", BT: "BREAK", P: "PENS" };

export default function MatchLive({ initial, formSlot, stakesSlot, teamStatusSlot }: Props) {
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

  const homeTeam = fixture.home_team ?? "Home";
  const awayTeam = fixture.away_team ?? "Away";
  const history = fixture.live_winprob_history ?? [];

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

      {fixture.live_read ? (
        <div className="live-read">
          <span className="an-eyebrow"><span className="lr-dot" aria-hidden="true" /> Live read</span>
          <p>{fixture.live_read}</p>
        </div>
      ) : null}

      {fixture.live_winprob ? (
        <>
          <h2 className="section-title">
            Win probability{" "}
            <span style={{ fontSize: 13, fontWeight: 700, color: "var(--status-live)", verticalAlign: "middle" }}>· live</span>
          </h2>
          <LiveWinProb
            forecast={fixture.forecast}
            live={fixture.live_winprob}
            homeTeam={homeTeam}
            awayTeam={awayTeam}
            minute={minute}
          />
        </>
      ) : null}

      {history.length >= 2 ? (
        <LiveWinProbChart
          history={history}
          homeTeam={homeTeam}
          awayTeam={awayTeam}
          homeScore={fixture.home_score}
          awayScore={fixture.away_score}
          minute={minute}
          redCards={countReds(fixture.events)}
        />
      ) : null}

      {fixture.forecast && fixture.forecast.factors.length > 0 ? (
        <>
          <h2 className="section-title">What drove the pre-match forecast</h2>
          <section className="forecast-card" aria-label="Signals behind the pre-match forecast">
            <p className="fc-intro" style={{ marginTop: 0 }}>
              The signals the model weighed before kickoff — the lean shows which side each favoured and why.
            </p>
            <ul className="fc-factors">
              {fixture.forecast.factors.map((f) => (
                <li className="fc-factor" key={f.name}>
                  <span className="ff-name">{f.name}</span>
                  <span className={`ff-lean ${f.lean}`}>
                    {f.lean === "home" ? `Favours ${homeTeam}` : f.lean === "away" ? `Edge ${awayTeam}` : "Even"}
                  </span>
                  <span className="ff-why">{f.why}</span>
                </li>
              ))}
            </ul>
            <p className="fc-note">
              The pre-match split is a <strong>model preview</strong>; the live model above is what updates during play.
            </p>
          </section>
        </>
      ) : null}

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
