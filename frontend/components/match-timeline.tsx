import type { ReactNode } from "react";
import type { MatchEvent } from "@/lib/api";
import { buildTimeline, subOnOff, eventKey } from "@/lib/match";

interface Props {
  events: MatchEvent[];
  homeTeam: string | null;
  awayTeam: string | null;
  // Event keys that arrived on the latest live poll — rendered with a transient
  // highlight. Undefined on the finished/preview views (no live polling).
  freshKeys?: Set<string>;
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
  if (t === "var") {
    return (
      <svg viewBox="0 0 16 16">
        <rect x="2.5" y="3.5" width="11" height="7.5" rx="1" fill="none" stroke="#6B7A9E" strokeWidth="1.3" />
        <path d="M6 13h4" stroke="#6B7A9E" strokeWidth="1.3" strokeLinecap="round" />
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
  if (t === "var") return detail ?? "VAR";
  return detail ?? type ?? "";
}

export default function MatchTimeline({ events, homeTeam, awayTeam, freshKeys }: Props) {
  const rows = buildTimeline(events);
  if (rows.length === 0) return null;

  return (
    <ul className="mt-list">
      {rows.map((r) => {
        const isGoal = r.score != null;
        const isSubst = (r.type ?? "").toLowerCase() === "subst";
        const chipSide = r.scoringSide ?? "";
        const minute = r.extra ? `${r.minute}+${r.extra}'` : `${r.minute}'`;
        const teamName = r.side === "home" ? homeTeam : r.side === "away" ? awayTeam : null;
        const meta = [
          typeLabel(r.type, r.detail),
          teamName,
          isGoal && r.assist ? `assist ${r.assist}` : null,
        ]
          .filter(Boolean)
          .join(" · ");
        const sub = isSubst ? subOnOff(r) : null;
        const fresh = freshKeys?.has(eventKey(r)) ?? false;
        return (
          <li className={`mt-item${isGoal ? " goal" : ""}${fresh ? " is-fresh" : ""}`} key={eventKey(r)}>
            <span className="mt-icon" aria-hidden="true">
              {icon(r.type, r.detail)}
            </span>
            <span className="mt-min">{minute}</span>
            <span className="mt-text">
              {sub ? (
                <strong>{sub.on ?? "—"}{sub.off ? ` ↔ ${sub.off}` : ""}</strong>
              ) : r.player ? (
                <strong>{r.player}</strong>
              ) : (
                <span>—</span>
              )}
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
