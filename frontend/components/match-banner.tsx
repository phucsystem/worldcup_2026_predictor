import type { ReactNode } from "react";
import Link from "next/link";
import type { FixtureRow, MatchEvent } from "@/lib/api";
import type { Forecast } from "@/lib/match";
import { sbsSearchUrl } from "@/lib/match";
import { bannerOutcome, forecastSegments, type BannerVariant } from "@/lib/banner";
import TeamFlag from "@/components/team-flag";
import FlagBackdrop from "@/components/flag-backdrop";
import MatchScorersStrip from "@/components/match-scorers-strip";
import ShareResultButton from "@/components/share-result-button";

interface Props {
  fixture: FixtureRow;
  variant: BannerVariant;
  /** Eyebrow text (e.g. "Next kickoff", "Live now · 64'", "Full Time · Group G"). */
  eyebrowLabel: ReactNode;
  /** Goal events — renders the scorer strip when present (live / final). */
  events?: MatchEvent[];
  /** Meta line content (kickoff time, group, etc.). */
  meta?: ReactNode;
  /** Win-probability forecast — renders the glanceable forecast bar (preview). */
  forecast?: Forecast | null;
  /** Variant extra rendered after meta, before the forecast bar (live clock / countdown). */
  belowMeta?: ReactNode;
  /** Home-only "View match analysis →" nav target. Detail heroes omit it (no self-link). */
  analysisHref?: string;
  /** Watch link visible label (e.g. "Watch live on SBS"). Omit to hide the link. */
  watchLabel?: string;
  /** Live styling for the watch link (pulsing dot vs ▶ play glyph). */
  watchLive?: boolean;
  /** Share button label (e.g. "Share result"). Omit to hide the button. */
  shareLabel?: string;
  /** Share sheet / image title. */
  shareTitle?: string;
}

// The single source for the match hero across every surface (home + detail,
// preview/live/final). Stays a server component while composing the client
// ShareResultButton as a child. The wrapper (<section>/<Link>) and its
// .is-live/.is-final class — which drive eyebrow + score coloring via
// globals.css — stay with the parent, as does the timer behaviour feeding the
// belowMeta slot (live clock / countdown).
export default function MatchBanner({
  fixture,
  variant,
  eyebrowLabel,
  events,
  meta,
  forecast,
  belowMeta,
  analysisHref,
  watchLabel,
  watchLive,
  shareLabel,
  shareTitle,
}: Props) {
  const hs = fixture.home_score ?? 0;
  const as = fixture.away_score ?? 0;
  const { homeCls, awayCls, showWL } = bannerOutcome(variant, hs, as);
  const seg = forecastSegments(forecast);
  const hasActions = analysisHref || watchLabel || shareLabel;
  const matchup = `${fixture.home_team ?? "this match"} v ${fixture.away_team ?? ""}`.trim();

  return (
    <>
      <FlagBackdrop home={fixture.home_team} away={fixture.away_team} />
      <span className="nm-eyebrow">
        <span className="dot" /> {eyebrowLabel}
      </span>
      <div className="nm-body">
        <span className={`nm-side${homeCls ? ` ${homeCls}` : ""}`}>
          <TeamFlag team={fixture.home_team} logo={fixture.home_logo} size={40} />
          {fixture.home_team ?? "TBD"}
          {showWL && homeCls === "win" ? <span className="nm-wl-tag win">W</span> : showWL && homeCls === "lose" ? <span className="nm-wl-tag lose">L</span> : null}
        </span>
        {variant === "preview" ? (
          <span className="nm-vs">VS</span>
        ) : (
          <span className="nm-score" aria-hidden="true">
            <span className={`nm-sc${homeCls ? ` ${homeCls}` : ""}`}>{hs}</span>
            <span className="nm-sc-sep">–</span>
            <span className={`nm-sc${awayCls ? ` ${awayCls}` : ""}`}>{as}</span>
          </span>
        )}
        <span className={`nm-side${awayCls ? ` ${awayCls}` : ""}`}>
          {showWL && awayCls === "win" ? <span className="nm-wl-tag win">W</span> : showWL && awayCls === "lose" ? <span className="nm-wl-tag lose">L</span> : null}
          {fixture.away_team ?? "TBD"}
          <TeamFlag team={fixture.away_team} logo={fixture.away_logo} size={40} />
        </span>
      </div>
      {events && events.length > 0 ? <MatchScorersStrip events={events} /> : null}
      {meta != null ? <div className="nm-meta">{meta}</div> : null}
      {belowMeta}
      {seg ? (
        <div
          className="nm-forecast"
          aria-label={`Win probability forecast (experimental): ${fixture.home_team ?? "home"} ${seg.homePct} percent, draw ${seg.drawPct} percent, ${fixture.away_team ?? "away"} ${seg.awayPct} percent`}
        >
          <span className="nm-fc-label">Win probability · experimental</span>
          <div className="nm-fc-bar">
            <span className="nm-fc-seg home" style={{ width: `${seg.homePct}%` }}>{seg.homePct}%</span>
            <span className="nm-fc-seg draw" style={{ width: `${seg.drawPct}%` }}>{seg.drawPct}%</span>
            <span className="nm-fc-seg away" style={{ width: `${seg.awayPct}%` }}>{seg.awayPct}%</span>
          </div>
        </div>
      ) : null}
      {hasActions ? (
        <div className="nm-actions">
          {analysisHref ? (
            <Link className="nm-cta" href={analysisHref} aria-label={`View ${matchup} match analysis`}>
              View match analysis →
            </Link>
          ) : null}
          {watchLabel ? (
            <a
              className="nm-watch"
              href={sbsSearchUrl(fixture.home_team, fixture.away_team)}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`${watchLabel}: ${matchup} (opens in a new tab)`}
            >
              {watchLive ? <span className="nw-dot" aria-hidden="true" /> : <span aria-hidden="true">▶</span>} {watchLabel}
            </a>
          ) : null}
          {shareLabel ? (
            <ShareResultButton fixtureId={fixture.fixture_id} label={shareLabel} shareTitle={shareTitle} />
          ) : null}
        </div>
      ) : null}
    </>
  );
}
