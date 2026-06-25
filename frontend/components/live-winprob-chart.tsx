import type { LiveWinProbPoint } from "@/lib/api";

interface Props {
  history: LiveWinProbPoint[];
  homeTeam: string;
  awayTeam: string;
  homeScore: number | null;
  awayScore: number | null;
  minute: number | null;
  redCards: number;
}

// Plot area within the 0 0 680 210 viewBox.
const X0 = 44;
const X1 = 664;
const Y0 = 20; // 100%
const Y1 = 178; // 0%
const FULL_TIME = 95; // x-axis anchor (regulation + avg stoppage), matches the model.

const xOf = (minute: number) => X0 + Math.max(0, Math.min(1, minute / FULL_TIME)) * (X1 - X0);
const yOf = (pct: number) => Y1 - Math.max(0, Math.min(100, pct)) * ((Y1 - Y0) / 100);

function goalSide(label: string | null | undefined, homeTeam: string, awayTeam: string): "home" | "away" | null {
  if (!label || !label.startsWith("Goal")) return null;
  if (label.includes(homeTeam)) return "home";
  if (label.includes(awayTeam)) return "away";
  return null;
}

// Win-probability swing chart: the home win % across the match, one point per
// significant event (lib/api live_winprob_history), with a gradient area fill, the
// 50% favourite line, goal markers, the current value as a KPI, and a faint
// "yet to play" band. Pure SVG; renders only when there are >= 2 points (guarded by
// the caller). All data comes from the history series — nothing is fabricated here.
export default function LiveWinProbChart({
  history,
  homeTeam,
  awayTeam,
  homeScore,
  awayScore,
  minute,
  redCards,
}: Props) {
  const pts = history.map((p) => ({ ...p, x: xOf(p.minute), y: yOf(p.home_pct) }));
  const now = pts[pts.length - 1];
  const line = pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const area = `M${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)} ` +
    pts.slice(1).map((p) => `L${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ") +
    ` L${now.x.toFixed(1)},${Y1} L${pts[0].x.toFixed(1)},${Y1} Z`;

  const minutesLeft = minute != null ? Math.max(0, FULL_TIME - minute) : null;
  const aria =
    `${homeTeam} win probability over the match: ` +
    pts.map((p) => `${p.home_pct}% at ${p.label || `${p.minute}'`}`).join(", ") +
    `. Currently ${now.home_pct}%.`;

  return (
    <section
      className="forecast-card"
      aria-label="How the win probability has moved during the match"
      style={{ marginBottom: "var(--space-6)" }}
    >
      <div className="fc-head">
        <h2 className="fc-title">How the odds have swung</h2>
        <span className="fc-tag" style={{ color: "var(--status-live)" }}>{homeTeam} win % · live</span>
      </div>
      <svg className="wp-chart" viewBox="0 0 680 210" preserveAspectRatio="xMidYMid meet" role="img" aria-label={aria}>
        <line x1={X0} y1={Y0} x2={X0} y2={Y1} stroke="var(--border-subtle, rgba(255,255,255,0.08))" strokeWidth={1} />
        <line x1={X0} y1={Y1} x2={X1} y2={Y1} stroke="var(--border-subtle, rgba(255,255,255,0.08))" strokeWidth={1} />
        <line x1={X0} y1={yOf(50)} x2={X1} y2={yOf(50)} stroke="var(--text-muted)" strokeWidth={1} strokeDasharray="3 4" opacity={0.5} />
        <text x={36} y={24} textAnchor="end" fontSize={10.5} fill="var(--text-muted)">100</text>
        <text x={36} y={yOf(50) + 4} textAnchor="end" fontSize={10.5} fill="var(--text-muted)">50</text>
        <text x={36} y={Y1 + 3} textAnchor="end" fontSize={10.5} fill="var(--text-muted)">0</text>

        {now.x < X1 ? (
          <>
            <rect x={now.x} y={Y0} width={X1 - now.x} height={Y1 - Y0} fill="rgba(255,255,255,0.035)" />
            {minutesLeft != null ? (
              <text x={(now.x + X1) / 2} y={Y0 + 14} textAnchor="middle" fontSize={10} fill="var(--text-muted)">
                ~{minutesLeft}' to play
              </text>
            ) : null}
          </>
        ) : null}

        <defs>
          <linearGradient id="wpFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent-bright)" stopOpacity={0.34} />
            <stop offset="100%" stopColor="var(--accent-bright)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <path d={area} fill="url(#wpFill)" />
        <polyline points={line} fill="none" stroke="var(--accent-bright)" strokeWidth={3} strokeLinejoin="round" strokeLinecap="round" />

        <line x1={now.x} y1={Y0} x2={now.x} y2={Y1} stroke="var(--status-live)" strokeWidth={1} strokeDasharray="2 3" opacity={0.6} />

        {pts.map((p, i) => {
          const side = goalSide(p.label, homeTeam, awayTeam);
          const isNow = i === pts.length - 1;
          if (isNow) {
            return (
              <g key={i}>
                <circle cx={p.x} cy={p.y} r={11} fill="var(--accent-bright)" opacity={0.18} />
                <circle cx={p.x} cy={p.y} r={5.5} fill="var(--accent-bright)" stroke="#06231A" strokeWidth={1.5} />
              </g>
            );
          }
          if (side === "away") return <circle key={i} cx={p.x} cy={p.y} r={4.5} fill="#FF5A5A" stroke="#06231A" strokeWidth={1} />;
          if (side === "home") return <circle key={i} cx={p.x} cy={p.y} r={4.5} fill="#2BD37E" stroke="#06231A" strokeWidth={1} />;
          return <circle key={i} cx={p.x} cy={p.y} r={3} fill="var(--text-muted)" />;
        })}

        <text x={now.x} y={Math.max(Y0 + 16, now.y - 14)} textAnchor="middle" fontSize={18} fontWeight={800} fill="var(--accent-bright)">
          {now.home_pct}%
        </text>

        {pts.map((p, i) => {
          const side = goalSide(p.label, homeTeam, awayTeam);
          const anchor = i === 0 ? "start" : "middle";
          const fill = i === pts.length - 1
            ? "var(--status-live)"
            : side === "away" ? "#FF5A5A" : side === "home" ? "#2BD37E" : "var(--text-muted)";
          return (
            <text key={i} x={p.x} y={196} textAnchor={anchor} fontSize={10.5} fontWeight={i === 0 ? 400 : 700} fill={fill}>
              {p.label || `${p.minute}'`}
            </text>
          );
        })}
      </svg>

      <div className="wp-inputs">
        <span className="wp-chip">Score <strong>{homeScore ?? 0}–{awayScore ?? 0}</strong></span>
        {minute != null ? <span className="wp-chip"><strong>{minute}'</strong> played</span> : null}
        {minutesLeft != null ? <span className="wp-chip"><strong>~{minutesLeft}'</strong> to play</span> : null}
        <span className="wp-chip"><strong>{redCards}</strong> red {redCards === 1 ? "card" : "cards"}</span>
        <span className="wp-chip">Pre-match prior · <strong>light weight</strong></span>
      </div>
      <p className="fc-note">
        A <strong>Python base model</strong> (score + minutes remaining) <strong>adjusted by an AI agent</strong> for
        live context — in-game events, live xG/shots, and team status — then bounded and re-normalised. It shifts each
        poll and on every goal. Illustrative estimate — not betting advice.
      </p>
    </section>
  );
}
