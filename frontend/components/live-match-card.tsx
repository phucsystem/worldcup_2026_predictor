"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type { FixtureRow, MatchEvent } from "@/lib/api";
import MatchBanner from "@/components/match-banner";
import ShareResultButton from "@/components/share-result-button";
import { liveMinute } from "@/lib/live";
import { sbsSearchUrl } from "@/lib/match";

// Initial may be a bare row (no events); polling the detail endpoint fills in
// goal events so the scorer strip matches the detail page.
type LiveFixture = FixtureRow & { events?: MatchEvent[] };

interface Props {
  initial: LiveFixture;
}

const POLL_MS = 30_000;
const TICK_MS = 1_000;
const SHORT_FROZEN: Record<string, string> = { HT: "HT", BT: "BREAK", P: "PENS" };

export default function LiveMatchCard({ initial }: Props) {
  const [fixture, setFixture] = useState<LiveFixture | null>(initial);
  // Seed from the server-provided anchor so SSR and first client render agree;
  // the 1s effect switches to the real wall clock after mount.
  const [nowMs, setNowMs] = useState<number>(() => {
    const t = initial.updated_at ? Date.parse(initial.updated_at) : NaN;
    return Number.isNaN(t) ? 0 : t;
  });
  const inFlight = useRef(false);

  useEffect(() => {
    const tick = setInterval(() => setNowMs(Date.now()), TICK_MS);
    return () => clearInterval(tick);
  }, []);

  // Poll the match detail (includes events) so the live score AND scorer strip
  // stay current. Runs once immediately so events appear without a full delay.
  useEffect(() => {
    let active = true;
    async function poll() {
      if (inFlight.current) return;
      inFlight.current = true;
      try {
        const res = await fetch(`/api/fixtures/${initial.fixture_id}`, { cache: "no-store" });
        if (!res.ok) return;
        const next: LiveFixture = await res.json();
        if (active) setFixture(next);
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
  }, [initial.fixture_id]);

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
    <section
      className="next-match is-live"
      data-flag-bg
      aria-label={`Live now: ${fixture.home_team ?? "TBD"} ${fixture.home_score ?? 0}, ${fixture.away_team ?? "TBD"} ${fixture.away_score ?? 0}, ${label}.`}
    >
      <MatchBanner
        fixture={fixture}
        variant="live"
        eyebrowLabel={`Live now · ${label}`}
        events={fixture.events}
        meta={fixture.group_name ?? fixture.stage ?? null}
      />
      <div className="nm-live-clock-wrap">
        <span className="nm-live-clock" aria-hidden="true">{clock}</span>
      </div>
      <div className="nm-actions">
        <a
          className="nm-watch"
          href={sbsSearchUrl(fixture.home_team, fixture.away_team)}
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
      <Link
        className="nm-cta"
        href={`/match/${fixture.fixture_id}`}
        aria-label={`View ${fixture.home_team ?? "this match"} v ${fixture.away_team ?? ""} match analysis`}
      >
        Match analysis →
      </Link>
    </section>
  );
}
