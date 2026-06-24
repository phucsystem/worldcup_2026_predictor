import type { FixtureDetail } from "@/lib/api";
import TeamFlag from "@/components/team-flag";
import LocalTime from "@/components/local-time";
import MatchScorersStrip from "@/components/match-scorers-strip";
import FlagBackdrop from "@/components/flag-backdrop";
import { sbsSearchUrl } from "@/lib/match";

interface Props {
  fixture: FixtureDetail;
}

const STATUS_LABEL: Record<string, string> = {
  FT: "Full Time",
  AET: "After Extra Time",
  PEN: "Penalties",
};

// Finished hero — the .is-final variant of the .next-match banner, so it stays
// consistent with the live (.is-live) and preview heroes (matches prototype S-10).
export default function MatchHeroFinal({ fixture }: Props) {
  const hs = fixture.home_score ?? 0;
  const as = fixture.away_score ?? 0;
  const homeWon = hs > as;
  const awayWon = as > hs;
  const homeCls = homeWon ? " win" : awayWon ? " lose" : "";
  const awayCls = awayWon ? " win" : homeWon ? " lose" : "";
  const statusLabel = STATUS_LABEL[(fixture.status ?? "").toUpperCase()] ?? "Full Time";
  const context = fixture.group_name ?? fixture.stage ?? null;

  return (
    <section
      className="next-match is-final"
      data-flag-bg
      aria-label={`Full time: ${fixture.home_team ?? "TBD"} ${hs}, ${fixture.away_team ?? "TBD"} ${as}`}
    >
      <FlagBackdrop home={fixture.home_team} away={fixture.away_team} />
      <span className="nm-eyebrow">
        <span className="dot" /> {statusLabel}
        {context ? ` · ${context}` : ""}
      </span>
      <div className="nm-body">
        <span className={`nm-side${homeCls}`}>
          <TeamFlag team={fixture.home_team} logo={fixture.home_logo} size={40} />
          {fixture.home_team ?? "TBD"}
          {homeWon ? <span className="nm-wl-tag win">W</span> : awayWon ? <span className="nm-wl-tag lose">L</span> : null}
        </span>
        <span className="nm-score" aria-hidden="true">
          <span className={`nm-sc${homeCls}`}>{hs}</span>
          <span className="nm-sc-sep">–</span>
          <span className={`nm-sc${awayCls}`}>{as}</span>
        </span>
        <span className={`nm-side${awayCls}`}>
          {awayWon ? <span className="nm-wl-tag win">W</span> : homeWon ? <span className="nm-wl-tag lose">L</span> : null}
          {fixture.away_team ?? "TBD"}
          <TeamFlag team={fixture.away_team} logo={fixture.away_logo} size={40} />
        </span>
      </div>
      <MatchScorersStrip events={fixture.events} />
      <div className="nm-meta">
        <LocalTime iso={fixture.kickoff_utc} mode="dayTime" withZone />
      </div>
      <div className="nm-watch-wrap">
        <a
          className="nm-watch"
          href={sbsSearchUrl(fixture.home_team, fixture.away_team)}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Find ${fixture.home_team ?? "this match"} v ${fixture.away_team ?? ""} highlights on SBS On Demand (opens in a new tab)`}
        >
          <span aria-hidden="true">▶</span> Watch highlights on SBS
        </a>
      </div>
    </section>
  );
}
