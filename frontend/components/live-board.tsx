"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type { FixtureRow } from "@/lib/api";
import { liveMinute } from "@/lib/live";
import { bannerOutcome } from "@/lib/banner";
import { sbsSearchUrl } from "@/lib/match";
import TeamFlag from "@/components/team-flag";
import ShareResultButton from "@/components/share-result-button";

interface Props {
  initial: FixtureRow[];
  /** Per-fixture qualification stake line, keyed by fixture_id. */
  stakes?: Record<number, string>;
}

const POLL_MS = 30_000;
const TICK_MS = 1_000;
const SHORT_FROZEN: Record<string, string> = { HT: "HT", BT: "BREAK", P: "PENS" };

// Compact board for 2+ concurrent in-progress matches. One island polls the
// batch /api/live endpoint (one request for every card) and runs a single 1s
// clock tick shared across all cards — the multi-match analogue of the single
// LiveMatchCard hero, which keeps the big banner for the one-live case.
export default function LiveBoard({ initial, stakes }: Props) {
  const [fixtures, setFixtures] = useState<FixtureRow[]>(initial);
  // Seed at 0 so SSR and first client render agree (liveMinute → elapsed with a
  // non-positive bump); the tick switches to the real wall clock after mount.
  const [nowMs, setNowMs] = useState<number>(0);
  const inFlight = useRef(false);

  useEffect(() => {
    const tick = setInterval(() => setNowMs(Date.now()), TICK_MS);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    let active = true;
    async function poll() {
      if (inFlight.current) return;
      inFlight.current = true;
      try {
        const res = await fetch("/api/live", { cache: "no-store" });
        if (!res.ok) return;
        const next: FixtureRow[] = await res.json();
        if (active) setFixtures(next);
      } catch {
        // keep the last good state on a transient failure
      } finally {
        inFlight.current = false;
      }
    }
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  if (fixtures.length === 0) return null;

  return (
    <div className="live-board">
      {fixtures.map((fixture) => (
        <LiveCard
          key={fixture.fixture_id}
          fixture={fixture}
          nowMs={nowMs}
          stake={stakes?.[fixture.fixture_id]}
        />
      ))}
    </div>
  );
}

function LiveCard({
  fixture,
  nowMs,
  stake,
}: {
  fixture: FixtureRow;
  nowMs: number;
  stake?: string;
}) {
  const hs = fixture.home_score ?? 0;
  const as = fixture.away_score ?? 0;
  const { homeCls, awayCls } = bannerOutcome("live", hs, as);
  const { minute, frozen, label } = liveMinute(
    fixture.elapsed,
    fixture.updated_at,
    fixture.status,
    nowMs,
  );
  const code = (fixture.status ?? "").toUpperCase();
  const clock = frozen
    ? SHORT_FROZEN[code] ?? label
    : minute != null
      ? `${minute}'`
      : "LIVE";
  const matchup = `${fixture.home_team ?? "this match"} v ${fixture.away_team ?? ""}`.trim();

  return (
    <article
      className="live-card"
      aria-label={`Live: ${fixture.home_team ?? "TBD"} ${hs}, ${fixture.away_team ?? "TBD"} ${as}, ${label}${fixture.group_name ? `, ${fixture.group_name}` : ""}.`}
    >
      <div className="lc-head">
        {fixture.group_name ? <span className="group-pill">{fixture.group_name}</span> : <span />}
        <span className="nm-live-clock lc-clock" aria-hidden="true">
          {clock}
        </span>
      </div>
      <div className="lc-body">
        <span className={`lc-side${homeCls ? ` ${homeCls}` : ""}`}>
          <TeamFlag team={fixture.home_team} logo={fixture.home_logo} size={22} />
          <span className="lc-name">{fixture.home_team ?? "TBD"}</span>
        </span>
        <span className="lc-score" aria-hidden="true">
          <span className={`lc-sc${homeCls ? ` ${homeCls}` : ""}`}>{hs}</span>
          <span className="lc-sc-sep">–</span>
          <span className={`lc-sc${awayCls ? ` ${awayCls}` : ""}`}>{as}</span>
        </span>
        <span className={`lc-side${awayCls ? ` ${awayCls}` : ""}`}>
          <span className="lc-name">{fixture.away_team ?? "TBD"}</span>
          <TeamFlag team={fixture.away_team} logo={fixture.away_logo} size={22} />
        </span>
      </div>
      {stake ? <p className="lc-stake">{stake}</p> : null}
      <div className="nm-actions">
        <Link
          className="nm-cta"
          href={`/match/${fixture.fixture_id}`}
          aria-label={`View ${matchup} match analysis`}
        >
          View match analysis →
        </Link>
        <a
          className="nm-watch"
          href={sbsSearchUrl(fixture.home_team, fixture.away_team)}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Watch live on SBS: ${matchup} (opens in a new tab)`}
        >
          <span className="nw-dot" aria-hidden="true" /> Watch live
        </a>
        <ShareResultButton
          fixtureId={fixture.fixture_id}
          label="Share"
          shareTitle={`${fixture.home_team ?? "TBD"} ${hs}–${as} ${fixture.away_team ?? "TBD"}`}
        />
      </div>
    </article>
  );
}
