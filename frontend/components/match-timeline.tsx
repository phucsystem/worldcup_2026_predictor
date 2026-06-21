import type { ReactNode } from "react";
import type { MatchEvent } from "@/lib/api";
import { buildTimeline } from "@/lib/match";

interface Props {
  events: MatchEvent[];
  homeTeam: string | null;
  awayTeam: string | null;
}

function icon(type: string | null, detail: string | null): ReactNode {
  const t = (type ?? "").toLowerCase();
  const d = (detail ?? "").toLowerCase();
  if (t === "goal") {
    return (
      <svg viewBox="0 0 16 16">
        <circle cx="8" cy="8" r="6" fill="#2BD37E" />
        <circle cx="8" cy="8" r="6" fill="none" stroke="#06231A" strokeWidth="0.5" />
      </svg>
    );
  }
  if (t === "card") {
    const fill = d.includes("red") ? "#FF5A5A" : "#F4B740";
    return (
      <svg viewBox="0 0 16 16">
        <rect x="4.5" y="2.5" width="7" height="11" rx="1.2" fill={fill} />
      </svg>
    );
  }
  if (t === "subst") {
    return (
      <svg viewBox="0 0 16 16">
        <path d="M3 6h7l-2-2M13 10H6l2 2" fill="none" stroke="#6B7A9E" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 16 16">
      <circle cx="8" cy="8" r="2.5" fill="#6B7A9E" />
    </svg>
  );
}

function typeLabel(type: string | null, detail: string | null): string {
  const t = (type ?? "").toLowerCase();
  if (t === "goal") return (detail ?? "").toLowerCase() === "own goal" ? "Own goal" : "Goal";
  if (t === "card") return detail ?? "Card";
  if (t === "subst") return "Sub";
  return detail ?? type ?? "";
}

export default function MatchTimeline({ events, homeTeam, awayTeam }: Props) {
  const rows = buildTimeline(events);
  if (rows.length === 0) return null;

  return (
    <ul className="mt-list">
      {rows.map((r, i) => {
        const isGoal = r.score != null;
        const chipSide = r.scoringSide ?? "";
        const minute = r.extra ? `${r.minute}+${r.extra}'` : `${r.minute}'`;
        const teamName = r.side === "home" ? homeTeam : r.side === "away" ? awayTeam : null;
        const meta = [typeLabel(r.type, r.detail), teamName].filter(Boolean).join(" · ");
        return (
          <li className={`mt-item${isGoal ? " goal" : ""}`} key={i}>
            <span className="mt-icon" aria-hidden="true">
              {icon(r.type, r.detail)}
            </span>
            <span className="mt-min">{minute}</span>
            <span className="mt-text">
              {r.player ? <strong>{r.player}</strong> : <span>—</span>}
              {meta ? <span className="mt-type">{meta}</span> : null}
            </span>
            {isGoal && r.score ? (
              <span className={`mt-score ${chipSide}`}>
                {r.score.home}–{r.score.away}
              </span>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
