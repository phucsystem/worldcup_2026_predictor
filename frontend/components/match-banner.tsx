import type { ReactNode } from "react";
import type { FixtureRow, MatchEvent } from "@/lib/api";
import TeamFlag from "@/components/team-flag";
import FlagBackdrop from "@/components/flag-backdrop";
import MatchScorersStrip from "@/components/match-scorers-strip";

type Variant = "preview" | "live" | "final";

interface Props {
  fixture: FixtureRow;
  variant: Variant;
  /** Eyebrow text (e.g. "Next kickoff", "Live now · 64'", "Full Time · Group G"). */
  eyebrowLabel: ReactNode;
  /** Goal events — renders the scorer strip when present (live / final). */
  events?: MatchEvent[];
  /** Meta line content (kickoff time, group, etc.). */
  meta?: ReactNode;
}

// Shared inner content for the .next-match hero across preview / live / final.
// The wrapper (Link vs section) and its .is-live/.is-final class — which drives
// eyebrow + score coloring via globals.css — stay with the parent, as do the
// variant extras (live clock, countdown, action buttons, CTA).
export default function MatchBanner({ fixture, variant, eyebrowLabel, events, meta }: Props) {
  const hs = fixture.home_score ?? 0;
  const as = fixture.away_score ?? 0;
  const isFinal = variant === "final";
  const homeWon = isFinal && hs > as;
  const awayWon = isFinal && as > hs;
  const homeCls = homeWon ? " win" : awayWon ? " lose" : "";
  const awayCls = awayWon ? " win" : homeWon ? " lose" : "";

  return (
    <>
      <FlagBackdrop home={fixture.home_team} away={fixture.away_team} />
      <span className="nm-eyebrow">
        <span className="dot" /> {eyebrowLabel}
      </span>
      <div className="nm-body">
        <span className={`nm-side${homeCls}`}>
          <TeamFlag team={fixture.home_team} logo={fixture.home_logo} size={40} />
          {fixture.home_team ?? "TBD"}
          {homeWon ? <span className="nm-wl-tag win">W</span> : awayWon ? <span className="nm-wl-tag lose">L</span> : null}
        </span>
        {variant === "preview" ? (
          <span className="nm-vs">VS</span>
        ) : (
          <span className="nm-score" aria-hidden="true">
            <span className={`nm-sc${homeCls}`}>{hs}</span>
            <span className="nm-sc-sep">–</span>
            <span className={`nm-sc${awayCls}`}>{as}</span>
          </span>
        )}
        <span className={`nm-side${awayCls}`}>
          {awayWon ? <span className="nm-wl-tag win">W</span> : homeWon ? <span className="nm-wl-tag lose">L</span> : null}
          {fixture.away_team ?? "TBD"}
          <TeamFlag team={fixture.away_team} logo={fixture.away_logo} size={40} />
        </span>
      </div>
      {events && events.length > 0 ? <MatchScorersStrip events={events} /> : null}
      {meta != null ? <div className="nm-meta">{meta}</div> : null}
    </>
  );
}
