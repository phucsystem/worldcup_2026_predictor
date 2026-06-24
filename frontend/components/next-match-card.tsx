import type { FixtureRow } from "@/lib/api";
import type { Forecast } from "@/lib/match";
import Countdown from "@/components/countdown";
import LocalTime from "@/components/local-time";
import MatchBanner from "@/components/match-banner";

interface Props {
  fixture: FixtureRow | null;
  forecast?: Forecast | null;
  stakeText?: string;
  // When false (e.g. rendered on the match page itself), omit the home-only
  // "View match analysis →" nav so the hero doesn't self-link.
  linked?: boolean;
}

export default function NextMatchCard({ fixture, forecast, stakeText, linked = true }: Props) {
  if (!fixture) return null;

  return (
    <section
      className="next-match"
      data-flag-bg
      aria-label={`Next match: ${fixture.home_team ?? "TBD"} vs ${fixture.away_team ?? "TBD"}.`}
    >
      <MatchBanner
        fixture={fixture}
        variant="preview"
        eyebrowLabel="Next kickoff"
        meta={
          <>
            <LocalTime iso={fixture.kickoff_utc} mode="dayTime" withZone />
            {fixture.group_name ? ` · ${fixture.group_name}` : ""}
          </>
        }
        belowMeta={
          <>
            <div className="nm-countdown-wrap">
              <span className="nm-cd-label">Kicks off in</span>
              <Countdown kickoffUtc={fixture.kickoff_utc} variant="tiles" />
            </div>
            {stakeText && <p className="nm-stake">{stakeText}</p>}
          </>
        }
        forecast={forecast}
        analysisHref={linked ? `/match/${fixture.fixture_id}` : undefined}
        shareLabel="Share forecast"
        shareTitle={`${fixture.home_team ?? "TBD"} vs ${fixture.away_team ?? "TBD"}`}
      />
    </section>
  );
}
