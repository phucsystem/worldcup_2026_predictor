import Link from "next/link";
import type { KnockoutBracket as Bracket, FixtureRow } from "@/lib/api";
import TeamFlag from "@/components/team-flag";
import EmptyState from "@/components/empty-state";

function TieTeam({ team, logo, score, winner }: { team: string | null; logo: string | null; score: number | null; winner: boolean }) {
  return (
    <div className="flex items-center gap-2 py-1">
      <TeamFlag team={team} logo={logo} size={18} />
      <span className="text-sm truncate flex-1" style={{ color: winner ? "#FFFFFF" : "#A9B6D4", fontWeight: winner ? 700 : 500 }}>
        {team ?? "TBD"}
      </span>
      {score != null && (
        <span className="text-sm font-bold tabular-nums" style={{ color: "#FFFFFF" }}>
          {score}
        </span>
      )}
    </div>
  );
}

function TieCard({ tie }: { tie: FixtureRow }) {
  const decided = tie.home_score != null && tie.away_score != null;
  const homeWon = decided && (tie.home_score as number) > (tie.away_score as number);
  const awayWon = decided && (tie.away_score as number) > (tie.home_score as number);
  return (
    <div className="px-3 py-2 border" style={{ backgroundColor: "#0A1B3D", borderColor: "#1E3157", borderRadius: "10px", minWidth: "220px" }}>
      <TieTeam team={tie.home_team} logo={tie.home_logo} score={tie.home_score} winner={homeWon} />
      <div style={{ borderTop: "1px solid #1E3157" }} />
      <TieTeam team={tie.away_team} logo={tie.away_logo} score={tie.away_score} winner={awayWon} />
      <Link
        href={`/match/${tie.fixture_id}`}
        className="block mt-2 text-xs font-semibold hover:underline focus-visible:rounded"
        style={{ color: "#4D8BFF" }}
        aria-label={`Match analysis: ${tie.home_team ?? "TBD"} vs ${tie.away_team ?? "TBD"}`}
      >
        Match analysis →
      </Link>
    </div>
  );
}

export default function KnockoutBracket({ bracket }: { bracket: Bracket }) {
  if (!bracket.rounds.length) {
    return (
      <EmptyState
        message="The knockout bracket fills in once the group stage concludes"
        subtext="Round of 16 → Final will appear here"
      />
    );
  }

  return (
    <div className="overflow-x-auto pb-2" style={{ WebkitOverflowScrolling: "touch" }}>
      <div className="flex gap-6" style={{ minWidth: "min-content" }}>
        {bracket.rounds.map((round) => (
          <section key={round.round} className="shrink-0" aria-label={round.round}>
            <h3 className="text-xs font-semibold uppercase mb-3" style={{ color: "#6B7A9E", letterSpacing: "0.04em" }}>
              {round.round}
            </h3>
            <div className="flex flex-col gap-3">
              {round.ties.map((tie) => (
                <TieCard key={tie.fixture_id} tie={tie} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
