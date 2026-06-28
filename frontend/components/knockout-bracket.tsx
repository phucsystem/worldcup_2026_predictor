import { Fragment } from "react";
import Link from "next/link";
import type { KnockoutBracket as Bracket, FixtureRow } from "@/lib/api";
import TeamFlag from "@/components/team-flag";
import LiveBadge from "@/components/live-badge";
import LocalTime from "@/components/local-time";
import EmptyState from "@/components/empty-state";
import { matchState } from "@/lib/match";

// Bracket geometry lives in real CSS classes (pseudo-free, explicit segments) so
// the connector columns can draw the ┤ tree without depending on card width.
// Each round body and each cell is flex:1 so card centers land at predictable
// fractions; a connector cell joins its two feeders (at 25%/75%) to the next
// round card (at 50%).
const KB_CSS = `
.kb-scroll{overflow-x:auto;padding-bottom:8px;-webkit-overflow-scrolling:touch}
.kb-bracket{display:flex;align-items:stretch;min-width:min-content}
.kb-round{display:flex;flex-direction:column}
.kb-conn{width:40px;flex:0 0 40px}
.kb-title{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#6B7A9E;margin-bottom:12px;white-space:nowrap;min-height:16px}
.kb-body{flex:1;display:flex;flex-direction:column;justify-content:space-around}
.kb-cell{flex:1;display:flex;align-items:center;padding:6px 0}
.kb-conn-cell{position:relative;padding:0}
.kb-h{position:absolute;border-top:2px solid #1E3157}
.kb-v{position:absolute;border-left:2px solid #1E3157}
.kb-card{display:block;width:208px;background:#0A1B3D;border:1px solid #1E3157;border-radius:12px;padding:10px 12px;text-decoration:none;transition:border-color .15s,background .15s}
.kb-card:hover{border-color:#2D6BF6;background:#0D2249}
.kb-card-static{cursor:default}
.kb-card-static:hover{border-color:#1E3157;background:#0A1B3D}
.kb-chead{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}
.kb-time{font-size:11px;color:#6B7A9E;white-space:nowrap}
.kb-badge{font-size:10px;font-weight:700;color:#A9B6D4;background:#13294F;border-radius:6px;padding:1px 6px;white-space:nowrap}
.kb-row{display:flex;align-items:center;gap:8px;padding:3px 0}
.kb-name{flex:1;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kb-score{font-size:14px;font-weight:700;font-variant-numeric:tabular-nums;color:#FFFFFF}
.kb-sep{height:1px;background:#1E3157;margin:2px 0}
`;

function statusBadge(status: string | null) {
  const st = matchState(status);
  if (st === "live") return <LiveBadge />;
  if (st === "finished")
    return <span className="kb-badge">{(status ?? "FT").toUpperCase()}</span>;
  return null;
}

function TieTeam({
  team,
  logo,
  score,
  winner,
}: {
  team: string | null;
  logo: string | null;
  score: number | null;
  winner: boolean;
}) {
  return (
    <div className="kb-row">
      <TeamFlag team={team} logo={logo} size={18} />
      <span
        className="kb-name"
        style={{ color: winner ? "#FFFFFF" : "#A9B6D4", fontWeight: winner ? 700 : 500 }}
      >
        {team ?? "TBD"}
      </span>
      {score != null && <span className="kb-score">{score}</span>}
    </div>
  );
}

function TieCard({ tie }: { tie: FixtureRow }) {
  const st = matchState(tie.status);
  const showScore =
    st !== "preview" && tie.home_score != null && tie.away_score != null;
  const homeWon = showScore && (tie.home_score as number) > (tie.away_score as number);
  const awayWon = showScore && (tie.away_score as number) > (tie.home_score as number);
  const body = (
    <>
      <div className="kb-chead">
        <LocalTime iso={tie.kickoff_utc} mode="dayTime" className="kb-time" />
        {statusBadge(tie.status)}
      </div>
      <TieTeam
        team={tie.home_team}
        logo={tie.home_logo}
        score={showScore ? tie.home_score : null}
        winner={homeWon}
      />
      <div className="kb-sep" />
      <TieTeam
        team={tie.away_team}
        logo={tie.away_logo}
        score={showScore ? tie.away_score : null}
        winner={awayWon}
      />
    </>
  );

  // Synthesized/placeholder ties (later rounds not yet in the feed) carry a
  // negative id and have no match page — render them as a plain card.
  if (tie.fixture_id <= 0) {
    return <div className="kb-card kb-card-static">{body}</div>;
  }
  return (
    <Link
      href={`/match/${tie.fixture_id}`}
      className="kb-card"
      aria-label={`Match analysis: ${tie.home_team ?? "TBD"} vs ${tie.away_team ?? "TBD"}`}
    >
      {body}
    </Link>
  );
}

// Winning team of a finished tie, by score; null if undecided or level (a
// penalty result isn't derivable from the score). Drives winner-path highlight.
function winnerOf(tie: FixtureRow | undefined): string | null {
  if (!tie || matchState(tie.status) !== "finished") return null;
  if (tie.home_score == null || tie.away_score == null) return null;
  if (tie.home_score > tie.away_score) return tie.home_team;
  if (tie.away_score > tie.home_score) return tie.away_team;
  return null;
}

const PATH_HI = "#4D8BFF"; // a winner has advanced along this edge
const PATH_BASE = "#1E3157";

// One connector cell joins two feeder cards (centred at 25%/75% of the cell) to
// the single next-round card (centred at 50%). An edge lights up once its feeder
// tie is decided, so the winner's path through the bracket is highlighted.
function ConnectorCell({ topWon, botWon }: { topWon: boolean; botWon: boolean }) {
  const top = topWon ? PATH_HI : PATH_BASE;
  const bot = botWon ? PATH_HI : PATH_BASE;
  const junction = topWon || botWon ? PATH_HI : PATH_BASE;
  return (
    <div className="kb-cell kb-conn-cell">
      <span className="kb-h" style={{ top: "25%", left: 0, width: "50%", borderTopColor: top }} />
      <span className="kb-h" style={{ top: "75%", left: 0, width: "50%", borderTopColor: bot }} />
      <span className="kb-v" style={{ left: "50%", top: "25%", height: "25%", borderLeftColor: top }} />
      <span className="kb-v" style={{ left: "50%", top: "50%", height: "25%", borderLeftColor: bot }} />
      <span className="kb-h" style={{ top: "50%", left: "50%", width: "50%", borderTopColor: junction }} />
    </div>
  );
}

export default function KnockoutBracket({ bracket }: { bracket: Bracket }) {
  const rounds = bracket.rounds;
  if (!rounds.length) {
    return (
      <EmptyState
        message="The knockout bracket fills in once the group stage concludes"
        subtext="Round of 32 → Final will appear here"
      />
    );
  }

  return (
    <div className="kb-scroll">
      <style>{KB_CSS}</style>
      <div className="kb-bracket">
        {rounds.map((round, ri) => {
          const next = rounds[ri + 1];
          // Only bridge when the next round is fully scheduled relative to this
          // one (count halves) — avoids misleading lines on a partial bracket.
          const bridge =
            next && round.ties.length > 1 &&
            next.ties.length === Math.ceil(round.ties.length / 2);
          return (
            <Fragment key={round.round}>
              <div className="kb-round">
                <div className="kb-title">{round.round}</div>
                <div className="kb-body">
                  {round.ties.map((tie) => (
                    <div className="kb-cell" key={tie.fixture_id}>
                      <TieCard tie={tie} />
                    </div>
                  ))}
                </div>
              </div>
              {bridge && (
                <div className="kb-round kb-conn">
                  <div className="kb-title">&nbsp;</div>
                  <div className="kb-body">
                    {next.ties.map((t, j) => (
                      <ConnectorCell
                        key={t.fixture_id}
                        topWon={winnerOf(round.ties[2 * j]) != null}
                        botWon={winnerOf(round.ties[2 * j + 1]) != null}
                      />
                    ))}
                  </div>
                </div>
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
