import type { Forecast } from "@/lib/match";
import type { LiveWinProb } from "@/lib/api";

interface Props {
  forecast: Forecast | null;
  live: LiveWinProb;
  homeTeam: string;
  awayTeam: string;
  minute: number | null;
}

const HOME_COLOR = "var(--accent-bright)";
const DRAW_COLOR = "var(--status-draw)";
const AWAY_COLOR = "#FF6B7A";

// 0% → x=120, 100% → x=600 (matches the prototype's scale).
const pctX = (pct: number) => 120 + Math.max(0, Math.min(100, pct)) * 4.8;

interface RowSpec {
  label: string;
  color: string;
  y: number;
  before: number | null;
  now: number;
}

function delta(before: number | null, now: number): { text: string; up: boolean } | null {
  if (before == null) return null;
  const d = now - before;
  if (d === 0) return null;
  return { text: `${d > 0 ? "▲" : "▼"} ${Math.abs(d)}`, up: d > 0 };
}

// Before-kickoff vs live win-probability as a slope/dumbbell chart: a faded dot for
// the pre-match split, a solid dot for the live number, one row per outcome. Pure
// presentation — the split is the hybrid Python+AI live number (lib/api live_winprob)
// and the pre-match forecast; this component adds no data of its own.
export default function LiveWinProb({ forecast, live, homeTeam, awayTeam, minute }: Props) {
  const rows: RowSpec[] = [
    { label: homeTeam, color: HOME_COLOR, y: 44, before: forecast?.home_pct ?? null, now: live.home },
    { label: "Draw", color: DRAW_COLOR, y: 90, before: forecast?.draw_pct ?? null, now: live.draw },
    { label: awayTeam, color: AWAY_COLOR, y: 136, before: forecast?.away_pct ?? null, now: live.away },
  ];

  const ariaParts = rows.map((r) =>
    r.before != null
      ? `${r.label} ${r.before}% to ${r.now}%`
      : `${r.label} ${r.now}%`,
  );
  const aria = `Win probability${forecast ? " before kickoff versus now" : ""}: ${ariaParts.join(", ")}.`;

  return (
    <section
      className="forecast-card"
      aria-label="Win probability — pre-match forecast versus live model"
      style={{ marginBottom: "var(--space-6)" }}
    >
      <div className="fc-head">
        <h2 className="fc-title">{forecast ? "Before kickoff → now" : "Win probability · live"}</h2>
        <span className="fc-tag" style={{ color: "var(--status-live)" }}>
          Live{minute != null ? ` · ${minute}'` : ""}
        </span>
      </div>
      <svg className="wp-chart" viewBox="0 0 680 180" preserveAspectRatio="xMidYMid meet" role="img" aria-label={aria}>
        <g stroke="rgba(255,255,255,0.06)" strokeWidth={1}>
          <line x1={120} y1={26} x2={120} y2={150} />
          <line x1={240} y1={26} x2={240} y2={150} />
          <line x1={480} y1={26} x2={480} y2={150} />
          <line x1={600} y1={26} x2={600} y2={150} />
        </g>
        <line x1={360} y1={22} x2={360} y2={150} stroke="var(--text-muted)" strokeWidth={1} strokeDasharray="3 4" opacity={0.55} />
        <text x={360} y={14} textAnchor="middle" fontSize={10} fill="var(--text-muted)">50% · favourite</text>
        <g fontSize={9.5} fill="var(--text-muted)" textAnchor="middle">
          <text x={120} y={168}>0</text>
          <text x={240} y={168}>25</text>
          <text x={360} y={168}>50</text>
          <text x={480} y={168}>75</text>
          <text x={600} y={168}>100%</text>
        </g>

        {rows.map((r) => {
          const nowX = pctX(r.now);
          const beforeX = r.before != null ? pctX(r.before) : null;
          const d = delta(r.before, r.now);
          return (
            <g key={r.label}>
              <line x1={120} y1={r.y} x2={600} y2={r.y} stroke="rgba(255,255,255,0.05)" strokeWidth={2} strokeLinecap="round" />
              {beforeX != null ? (
                <>
                  <line
                    x1={Math.min(beforeX, nowX)} y1={r.y} x2={Math.max(beforeX, nowX)} y2={r.y}
                    stroke={r.color} strokeWidth={4} strokeLinecap="round" opacity={0.6}
                  />
                  <circle cx={beforeX} cy={r.y} r={5} fill={r.color} opacity={0.45} />
                  <text x={beforeX} y={r.y - 11} textAnchor="middle" fontSize={10.5} fill="var(--text-muted)">{r.before}%</text>
                </>
              ) : null}
              <circle cx={nowX} cy={r.y} r={6.5} fill={r.color} />
              <text x={104} y={r.y + 4} textAnchor="end" fontSize={13} fontWeight={800} fill={r.color}>{r.label}</text>
              <text x={nowX} y={r.y - 11} textAnchor="middle" fontSize={13} fontWeight={800} fill={r.color}>{r.now}%</text>
              {d ? (
                <text x={626} y={r.y + 4} textAnchor="start" fontSize={12} fontWeight={800} fill={d.up ? "var(--status-live)" : "var(--text-muted)"}>
                  {d.text}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      <p className="fc-note" style={{ marginTop: "var(--space-2)" }}>
        {forecast ? "Faded dot = before kickoff, solid dot = now. " : ""}
        Live is a Python base model (score + minutes remaining) adjusted by AI for in-game
        context, bounded and re-normalised{forecast ? "; pre-match is a model preview" : ""}.
      </p>
    </section>
  );
}
