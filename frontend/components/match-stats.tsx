import type { MatchStat } from "@/lib/api";

interface Props {
  stats: MatchStat[];
  homeTeam: string | null;
  awayTeam: string | null;
}

// S-10 stat bars. Percentages are computed server-side (normalize_statistics);
// this only renders them. The higher side gets the `lead` highlight; an exact tie
// highlights neither. Returns null when there are no stats (graceful degradation).
export default function MatchStats({ stats, homeTeam, awayTeam }: Props) {
  if (!stats || stats.length === 0) return null;
  return (
    <div className="stat-bars">
      {stats.map((s) => {
        const homeLead = s.home_pct > s.away_pct;
        const awayLead = s.away_pct > s.home_pct;
        return (
          <div className="sb-row" key={s.label}>
            <div className="sb-top">
              <span className={`sb-val home${homeLead ? " lead" : ""}`}>{s.home}</span>
              <span className="sb-label">{s.label}</span>
              <span className={`sb-val away${awayLead ? " lead" : ""}`}>{s.away}</span>
            </div>
            <div
              className="sb-track"
              role="img"
              aria-label={`${s.label}: ${homeTeam ?? "home"} ${s.home}, ${awayTeam ?? "away"} ${s.away}`}
            >
              <span className="sb-fill home" style={{ width: `${s.home_pct}%` }} />
              <span className="sb-fill away" style={{ width: `${s.away_pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
