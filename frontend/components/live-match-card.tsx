"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type { FixtureRow } from "@/lib/api";
import TeamFlag from "@/components/team-flag";
import FlagBackdrop from "@/components/flag-backdrop";
import ShareResultButton from "@/components/share-result-button";
import { liveMinute } from "@/lib/live";

interface Props {
  initial: FixtureRow;
}

const POLL_MS = 30_000;
const TICK_MS = 1_000;

const SHORT_FROZEN: Record<string, string> = { HT: "HT", BT: "BREAK", P: "PENS" };

export default function LiveMatchCard({ initial }: Props) {
  const [fixture, setFixture] = useState<FixtureRow | null>(initial);
  // Seed from the server-provided anchor so SSR and first client render agree;
  // the 1s effect switches to the real wall clock after mount.
  const [nowMs, setNowMs] = useState<number>(() => {
    const t = initial.updated_at ? Date.parse(initial.updated_at) : NaN;
    return Number.isNaN(t) ? 0 : t;
  });
  const inFlight = useRef(false);

  // Tick the wall clock each second. nowMs is seeded from updated_at, so the
  // first render shows the real elapsed minute; the interval then interpolates.
  useEffect(() => {
    const tick = setInterval(() => setNowMs(Date.now()), TICK_MS);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    async function poll() {
      if (inFlight.current) return;
      inFlight.current = true;
      try {
        const res = await fetch("/api/live", { cache: "no-store" });
        if (!res.ok) return;
        const list: FixtureRow[] = await res.json();
        setFixture(list.length > 0 ? list[0] : null); // soonest-kicked first from the API
      } catch {
        // keep the last good state on a transient failure
      } finally {
        inFlight.current = false;
      }
    }
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, []);

  if (!fixture) return null;

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

  return (
    <>
      <Link
        className="next-match is-live"
        data-flag-bg
        href={`/match/${fixture.fixture_id}`}
        aria-label={`Live now: ${fixture.home_team ?? "TBD"} ${fixture.home_score ?? 0}, ${fixture.away_team ?? "TBD"} ${fixture.away_score ?? 0}, ${label}. View match analysis.`}
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
      <div className="nm-meta">{fixture.group_name ?? "Live"}</div>
      <div className="nm-live-clock-wrap">
        <span className="nm-live-clock" aria-hidden="true">{clock}</span>
      </div>
      <span className="nm-cta">Match analysis →</span>
      </Link>
      <div className="nm-actions">
        <ShareResultButton
          fixtureId={fixture.fixture_id}
          label="Share live score"
          shareTitle={`${fixture.home_team ?? "TBD"} ${fixture.home_score ?? 0}–${fixture.away_score ?? 0} ${fixture.away_team ?? "TBD"}`}
        />
      </div>
    </>
  );
}
