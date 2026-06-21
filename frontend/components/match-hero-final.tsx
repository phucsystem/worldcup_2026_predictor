import type { FixtureRow } from "@/lib/api";
import TeamFlag from "@/components/team-flag";

interface Props {
  fixture: FixtureRow;
}

const STATUS_LABEL: Record<string, string> = {
  FT: "Full time",
  AET: "After extra time",
  PEN: "Penalties",
};

export default function MatchHeroFinal({ fixture }: Props) {
  const hs = fixture.home_score ?? 0;
  const as = fixture.away_score ?? 0;
  const homeWon = hs > as;
  const awayWon = as > hs;
  const statusLabel = STATUS_LABEL[(fixture.status ?? "").toUpperCase()] ?? "Full time";
  const context = fixture.group_name ?? fixture.stage ?? null;

  return (
    <section
      className="match-hero"
      aria-label={`Final score: ${fixture.home_team ?? "TBD"} ${hs}, ${fixture.away_team ?? "TBD"} ${as}`}
    >
      <div className="mh-eyebrow">
        <span className="mh-tag">FT</span>
        <span>{statusLabel}</span>
        {context ? (
          <>
            <span className="mh-sep">·</span>
            <span>{context}</span>
          </>
        ) : null}
      </div>
      <div className="mh-body">
        <span className={`mh-team home${homeWon ? "" : awayWon ? " lose" : ""}`}>
          {fixture.home_team ?? "TBD"}
          <TeamFlag team={fixture.home_team} logo={fixture.home_logo} size={40} />
        </span>
        <span className="mh-score" aria-hidden="true">
          <span className={homeWon ? "ms-win" : awayWon ? "ms-lose" : undefined}>{hs}</span>
          <span className="mh-dash">–</span>
          <span className={awayWon ? "ms-win" : homeWon ? "ms-lose" : undefined}>{as}</span>
        </span>
        <span className={`mh-team away${awayWon ? "" : homeWon ? " lose" : ""}`}>
          <TeamFlag team={fixture.away_team} logo={fixture.away_logo} size={40} />
          {fixture.away_team ?? "TBD"}
        </span>
      </div>
    </section>
  );
}
