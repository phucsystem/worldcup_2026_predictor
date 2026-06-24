import Link from "next/link";
import type { FixtureRow } from "@/lib/api";
import Countdown from "@/components/countdown";
import LocalTime from "@/components/local-time";
import MatchBanner from "@/components/match-banner";

interface Props {
  fixture: FixtureRow | null;
  stakeText?: string;
  // When false (e.g. rendered on the match page itself), drop the wrapping link
  // + CTA so the hero doesn't self-link.
  linked?: boolean;
}

export default function NextMatchCard({ fixture, stakeText, linked = true }: Props) {
  if (!fixture) return null;

  const body = (
    <>
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
      />
      <div className="nm-countdown-wrap">
        <span className="nm-cd-label">Kicks off in</span>
        <Countdown kickoffUtc={fixture.kickoff_utc} variant="tiles" />
      </div>
      {stakeText && <p className="nm-stake">{stakeText}</p>}
      {linked && <span className="nm-cta">Match analysis →</span>}
    </>
  );

  if (!linked) {
    return (
      <section
        className="next-match"
        data-flag-bg
        aria-label={`Next match: ${fixture.home_team ?? "TBD"} vs ${fixture.away_team ?? "TBD"}.`}
      >
        {body}
      </section>
    );
  }

  return (
    <Link
      className="next-match"
      data-flag-bg
      href={`/match/${fixture.fixture_id}`}
      aria-label={`Next match: ${fixture.home_team ?? "TBD"} vs ${fixture.away_team ?? "TBD"}. View match analysis.`}
    >
      {body}
    </Link>
  );
}
