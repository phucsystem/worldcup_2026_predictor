import type { MatchEvent } from "@/lib/api";
import { goalscorers } from "@/lib/match";

interface Props {
  events: MatchEvent[];
}

// The in-banner goalscorer strip (home right-aligned, away left-aligned) shared
// by the live and finished match heroes. Renders nothing without goals.
export default function MatchScorersStrip({ events }: Props) {
  const scorers = goalscorers(events);
  if (scorers.length === 0) return null;
  const home = scorers.filter((s) => s.side === "home");
  const away = scorers.filter((s) => s.side === "away");
  const mins = (m: number[]) => m.map((x) => `${x}'`).join(", ");

  return (
    <div className="nm-scorers" aria-label="Goalscorers">
      <div className="nm-sc-side home">
        {home.map((s, i) => (
          <span className="nm-sc-goal" key={i}>
            <span className="nm-sc-ball" aria-hidden="true">⚽</span> {s.player}{" "}
            <span className="nm-sc-t">{mins(s.minutes)}</span>
          </span>
        ))}
      </div>
      <div className="nm-sc-side away">
        {away.map((s, i) => (
          <span className="nm-sc-goal" key={i}>
            <span className="nm-sc-t">{mins(s.minutes)}</span> {s.player}{" "}
            <span className="nm-sc-ball" aria-hidden="true">⚽</span>
          </span>
        ))}
      </div>
    </div>
  );
}
