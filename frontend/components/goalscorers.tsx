import type { MatchEvent } from "@/lib/api";
import { goalscorers, type ScorerGoal } from "@/lib/match";
import { flagPrimaryColor, avatarTextColor } from "@/lib/flags";
import TeamFlag from "@/components/team-flag";

interface Props {
  events: MatchEvent[];
  homeTeam: string | null;
  awayTeam: string | null;
  homeLogo: string | null;
  awayLogo: string | null;
}

function initials(name: string | null): string {
  if (!name) return "—";
  const parts = name.trim().split(/\s+/);
  const letters = parts.length >= 2 ? parts[0][0] + parts[1][0] : name.trim().slice(0, 2);
  return letters.toUpperCase();
}

// Goal pill text from data-backed fields only: minute, plus the API goal detail
// when it adds meaning (penalty/own goal — not "Normal Goal"), plus the assister.
function goalLabel(g: ScorerGoal): string {
  const parts = [`${g.minute}'`];
  const detail = (g.detail ?? "").trim();
  if (detail && detail.toLowerCase() !== "normal goal") parts.push(detail);
  if (g.assist) parts.push(`assist ${g.assist}`);
  return parts.join(" · ");
}

// Scorer cards matching the design: colored team-initial avatar, inline flag,
// and per-goal pills. Role/shirt#/notes from the prototype are omitted — not
// data-backed by MatchEvent.
export default function Goalscorers({ events, homeTeam, awayTeam, homeLogo, awayLogo }: Props) {
  const scorers = goalscorers(events);
  if (scorers.length === 0) return null;
  return (
    <div className="scorers">
      {scorers.map((s, i) => {
        const isHome = s.side === "home";
        const team = isHome ? homeTeam : awayTeam;
        const logo = isHome ? homeLogo : awayLogo;
        const bg = flagPrimaryColor(team) ?? "#3A4668";
        return (
          <div className={`scorer-card${isHome ? "" : " opp"}`} key={`${s.side}-${s.player}-${i}`}>
            <span className="kp-avatar" style={{ background: bg, color: avatarTextColor(bg) }} aria-hidden="true">
              {initials(s.player)}
            </span>
            <div className="scorer-info">
              <div className="scorer-name">
                <TeamFlag team={team} logo={logo} size={18} />
                {s.player ?? "—"}
              </div>
              <div className="scorer-goals">
                {s.goals.map((g, j) => (
                  <span className="scorer-goal" key={j}>
                    ⚽ {goalLabel(g)}
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
