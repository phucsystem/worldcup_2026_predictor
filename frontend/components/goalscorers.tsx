import type { MatchEvent } from "@/lib/api";
import { goalscorers } from "@/lib/match";
import TeamFlag from "@/components/team-flag";

interface Props {
  events: MatchEvent[];
  homeTeam: string | null;
  awayTeam: string | null;
  homeLogo: string | null;
  awayLogo: string | null;
}

// Basic scorer cards from goalscorers(events): flag, name, minute(s). No role,
// shirt number, photo, or notes — those prototype fields are not data-backed.
export default function Goalscorers({ events, homeTeam, awayTeam, homeLogo, awayLogo }: Props) {
  const scorers = goalscorers(events);
  if (scorers.length === 0) return null;
  return (
    <div className="scorers">
      {scorers.map((s, i) => {
        const isHome = s.side === "home";
        const team = isHome ? homeTeam : awayTeam;
        const logo = isHome ? homeLogo : awayLogo;
        return (
          <div className={`scorer-card${isHome ? "" : " opp"}`} key={`${s.side}-${s.player}-${i}`}>
            <TeamFlag team={team} logo={logo} size={46} />
            <div className="scorer-info">
              <div className="scorer-name">{s.player ?? "—"}</div>
              <div className="scorer-goals">
                {s.minutes.map((m, j) => (
                  <span className="scorer-goal" key={j}>
                    ⚽ {m}&apos;
                  </span>
                ))}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
