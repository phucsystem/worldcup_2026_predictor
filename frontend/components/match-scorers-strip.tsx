import type { MatchEvent } from "@/lib/api";
import { goalscorers, type ScorerGoal } from "@/lib/match";

interface Props {
  events: MatchEvent[];
}

// Compact penalty / own-goal marker for the strip, mirroring goalLabel() in
// goalscorers.tsx. Open-play goals get no marker.
function goalMark(detail: string | null): string {
  const d = (detail ?? "").toLowerCase();
  if (d === "penalty") return " (pen)";
  if (d === "own goal") return " (o.g.)";
  return "";
}

const goalsText = (goals: ScorerGoal[]) =>
  goals.map((g) => `${g.minute}'${goalMark(g.detail)}`).join(", ");

// The in-banner goalscorer strip (home right-aligned, away left-aligned) shared
// by the live and finished match heroes. Renders nothing without goals.
export default function MatchScorersStrip({ events }: Props) {
  const scorers = goalscorers(events);
  if (scorers.length === 0) return null;
  const home = scorers.filter((s) => s.side === "home");
  const away = scorers.filter((s) => s.side === "away");

  return (
    <div className="nm-scorers" aria-label="Goalscorers">
      <div className="nm-sc-side home">
        {home.map((s, i) => (
          <span className="nm-sc-goal" key={i}>
            <span className="nm-sc-ball" aria-hidden="true">⚽</span> {s.player}{" "}
            <span className="nm-sc-t">{goalsText(s.goals)}</span>
          </span>
        ))}
      </div>
      <div className="nm-sc-side away">
        {away.map((s, i) => (
          <span className="nm-sc-goal" key={i}>
            <span className="nm-sc-t">{goalsText(s.goals)}</span> {s.player}{" "}
            <span className="nm-sc-ball" aria-hidden="true">⚽</span>
          </span>
        ))}
      </div>
    </div>
  );
}
