import Link from "next/link";
import type { FixtureRow } from "@/lib/api";
import TeamFlag from "@/components/team-flag";
import Countdown from "@/components/countdown";
import LocalTime from "@/components/local-time";

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
      <span className="nm-eyebrow">
        <span className="dot" /> Next kickoff
      </span>
      <div className="nm-body">
        <span className="nm-side">
          <TeamFlag team={fixture.home_team} logo={fixture.home_logo} size={40} />
          {fixture.home_team ?? "TBD"}
        </span>
        <span className="nm-vs">VS</span>
        <span className="nm-side">
          {fixture.away_team ?? "TBD"}
          <TeamFlag team={fixture.away_team} logo={fixture.away_logo} size={40} />
        </span>
      </div>
      <div className="nm-meta">
        <LocalTime iso={fixture.kickoff_utc} mode="dayTime" withZone />
        {fixture.group_name ? ` · ${fixture.group_name}` : ""}
      </div>
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
        aria-label={`Next match: ${fixture.home_team ?? "TBD"} vs ${fixture.away_team ?? "TBD"}.`}
      >
        {body}
      </section>
    );
  }

  return (
    <Link
      className="next-match"
      href={`/match/${fixture.fixture_id}`}
      aria-label={`Next match: ${fixture.home_team ?? "TBD"} vs ${fixture.away_team ?? "TBD"}. View match analysis.`}
    >
      {body}
    </Link>
  );
}
