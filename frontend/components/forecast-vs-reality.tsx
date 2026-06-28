import type { Forecast } from "@/lib/match";
import type { ForecastSignals, MatchStat } from "@/lib/api";

const HOME_COLOR = "var(--accent-bright)";
const DRAW_COLOR = "var(--status-draw)";
const AWAY_COLOR = "#FF6B7A";

type Side = "home" | "draw" | "away";
type Tone = "ontrack" | "tightening" | "upset";

interface VerdictResult {
  label: string;
  tone: Tone;
  text: string;
}

interface Props {
  forecast: Forecast;
  forecastSignals?: ForecastSignals | null;
  homeScore: number | null;
  awayScore: number | null;
  elapsed: number | null;
  homeTeam: string;
  awayTeam: string;
  statistics?: MatchStat[];
  liveRead?: string | null;
}

function forecastPick(forecast: Forecast): { side: Side; pct: number } {
  const { home_pct, draw_pct, away_pct } = forecast;
  if (home_pct >= draw_pct && home_pct >= away_pct) return { side: "home", pct: home_pct };
  if (away_pct >= draw_pct) return { side: "away", pct: away_pct };
  return { side: "draw", pct: draw_pct };
}

function actualState(homeScore: number | null, awayScore: number | null): Side {
  const h = homeScore ?? 0;
  const a = awayScore ?? 0;
  if (h > a) return "home";
  if (a > h) return "away";
  return "draw";
}

function verdict(pick: Side, state: Side, elapsed: number | null): VerdictResult {
  const late = (elapsed ?? 0) >= 75;
  const timeTag = late ? " — with time running out" : "";

  if (pick === "draw") {
    if (state === "draw") {
      return { label: "On track", tone: "ontrack", text: "Match is level, as the draw forecast expected." };
    }
    return { label: "Breaking the forecast", tone: "upset", text: `A draw was forecast but a side is now leading${timeTag}.` };
  }

  if (pick === state) {
    const label = late ? "Holding on" : "On track";
    return { label, tone: "ontrack", text: `The favoured side is leading${timeTag}.` };
  }

  if (state === "draw") {
    return { label: "Tighter than forecast", tone: "tightening", text: `The favoured side is level${timeTag}.` };
  }

  return { label: "Upset in progress", tone: "upset", text: `The favoured side is trailing${timeTag}.` };
}

const TONE_STYLES: Record<Tone, { bg: string; color: string; border: string }> = {
  ontrack:    { bg: "rgba(43, 211, 126, 0.12)",  color: "var(--status-live)", border: "var(--status-live)" },
  tightening: { bg: "rgba(244, 183, 64, 0.12)",  color: "var(--status-draw)", border: "var(--status-draw)" },
  upset:      { bg: "rgba(255, 90, 90, 0.12)",   color: "var(--status-loss)", border: "var(--status-loss)" },
};

const TONE_ICONS: Record<Tone, string> = { ontrack: "✅", tightening: "⚖️", upset: "🚨" };

// ---- Signal bar helpers ----

function formPoints(form: string): number {
  let pts = 0;
  for (const c of form) {
    if (c === "W") pts += 3;
    else if (c === "D") pts += 1;
  }
  return pts;
}

interface StatBarProps {
  homeVal: number;
  awayVal: number;
  invert?: boolean; // for FIFA rank: lower is better
}

function barWidths({ homeVal, awayVal, invert }: StatBarProps): { hp: number; ap: number } {
  let h = homeVal;
  let a = awayVal;
  if (invert) {
    // Treat "lower rank = stronger" by inverting so the better-ranked side gets the longer bar.
    // Use a fixed reference (50) so a rank of 1 vs 50 gives sensible proportions.
    h = Math.max(0, 50 - homeVal);
    a = Math.max(0, 50 - awayVal);
  }
  const total = h + a;
  if (total === 0) return { hp: 50, ap: 50 };
  const hp = Math.round((h / total) * 100);
  return { hp, ap: 100 - hp };
}

interface SignalRowProps {
  homeText: string;
  awayText: string;
  label: string;
  homeVal: number;
  awayVal: number;
  invert?: boolean;
}

function SignalRow({ homeText, awayText, label, homeVal, awayVal, invert }: SignalRowProps) {
  const { hp, ap } = barWidths({ homeVal, awayVal, invert });
  return (
    <div className="fvr-stat-row">
      <div className="fvr-stat-head">
        <span className="fvr-stat-val">{homeText}</span>
        <span className="fvr-stat-label">{label}</span>
        <span className="fvr-stat-val">{awayText}</span>
      </div>
      <div className="fvr-stat-bar">
        <div className="fvr-stat-seg fvr-stat-seg-home" style={{ width: `${hp}%` }} />
        <div className="fvr-stat-seg fvr-stat-seg-away" style={{ width: `${ap}%` }} />
      </div>
    </div>
  );
}

// ---- Stat type labels that match normalize_statistics output ----
const POSS_LABEL = "Possession";
const SHOTS_LABEL = "Shots";
const XG_LABEL = "Expected goals (xG)";

function findStat(stats: MatchStat[], label: string): MatchStat | undefined {
  return stats.find((s) => s.label === label);
}

function parseStatNum(val: string): number {
  return parseFloat(val.replace("%", "")) || 0;
}

export default function ForecastVsReality({
  forecast,
  forecastSignals,
  homeScore,
  awayScore,
  elapsed,
  homeTeam,
  awayTeam,
  statistics = [],
  liveRead,
}: Props) {
  const pick = forecastPick(forecast);
  const state = actualState(homeScore, awayScore);
  const v = verdict(pick.side, state, elapsed);
  const tone = TONE_STYLES[v.tone];

  const pickLabel =
    pick.side === "home" ? `${homeTeam} to win` :
    pick.side === "away" ? `${awayTeam} to win` :
    "Draw";

  const leaderLabel =
    state === "home" ? <><b>{homeTeam}</b> leading</> :
    state === "away" ? <><b>{awayTeam}</b> leading</> :
    <>Level — <b>no leader</b></>;

  const scoreline = `${homeTeam} ${homeScore ?? 0} – ${awayScore ?? 0} ${awayTeam}`;

  const { home_pct, draw_pct, away_pct } = forecast;

  // KEY SIGNALS for forecast column
  const sig = forecastSignals;
  const homeRank = sig?.home?.fifa_rank ?? null;
  const awayRank = sig?.away?.fifa_rank ?? null;
  const homeForm = sig?.home?.form ?? null;
  const awayForm = sig?.away?.form ?? null;
  const homeGpg = sig?.home?.goals_per_game ?? null;
  const awayGpg = sig?.away?.goals_per_game ?? null;
  const hasSignals = sig != null && (homeRank != null || homeForm != null || homeGpg != null
    || awayRank != null || awayForm != null || awayGpg != null);

  // LIVE STATS for reality column
  const possStat = findStat(statistics, POSS_LABEL);
  const shotsStat = findStat(statistics, SHOTS_LABEL);
  const xgStat = findStat(statistics, XG_LABEL);
  const hasLiveStats = !!(possStat || shotsStat || xgStat);

  return (
    <section className="forecast-card fvr-card" aria-label="Forecast vs Reality comparison">
      <div className="fvr-grid">
        {/* FORECAST column */}
        <div className="fvr-col">
          <div className="fvr-col-label">Forecast — pre-kickoff</div>
          <div className="fvr-pick">
            {pickLabel}{" "}
            <span style={{ color: "var(--accent-bright)" }}>{pick.pct}%</span>
          </div>
          <div className="fvr-pick-sub">Model call before first whistle</div>

          {/* 1X2 split bar */}
          <div className="fvr-split-bar" role="img" aria-label={`${homeTeam} ${home_pct}%, Draw ${draw_pct}%, ${awayTeam} ${away_pct}%`}>
            <div className="fvr-seg" style={{ width: `${home_pct}%`, background: HOME_COLOR }} />
            <div className="fvr-seg" style={{ width: `${draw_pct}%`, background: DRAW_COLOR }} />
            <div className="fvr-seg" style={{ width: `${away_pct}%`, background: AWAY_COLOR }} />
          </div>
          <div className="fvr-split-legend">
            <span><span className="fvr-swatch" style={{ background: HOME_COLOR }} />{homeTeam} {home_pct}%</span>
            <span><span className="fvr-swatch" style={{ background: DRAW_COLOR }} />Draw {draw_pct}%</span>
            <span><span className="fvr-swatch" style={{ background: AWAY_COLOR }} />{awayTeam} {away_pct}%</span>
          </div>

          {/* KEY SIGNALS — bottom-aligned via margin-top:auto */}
          {hasSignals && (
            <div className="fvr-stats-block">
              <div className="fvr-stats-caption">Key signals</div>
              {homeRank != null && awayRank != null && (
                <SignalRow
                  homeText={`#${homeRank}`}
                  awayText={`#${awayRank}`}
                  label="FIFA rank"
                  homeVal={homeRank}
                  awayVal={awayRank}
                  invert
                />
              )}
              {homeForm != null && awayForm != null && (
                <SignalRow
                  homeText={homeForm}
                  awayText={awayForm}
                  label="Form (last 5)"
                  homeVal={formPoints(homeForm)}
                  awayVal={formPoints(awayForm)}
                />
              )}
              {homeGpg != null && awayGpg != null && (
                <SignalRow
                  homeText={String(homeGpg)}
                  awayText={String(awayGpg)}
                  label="Goals / game"
                  homeVal={homeGpg}
                  awayVal={awayGpg}
                />
              )}
            </div>
          )}
        </div>

        <div className="fvr-divider" aria-hidden="true" />

        {/* REALITY column */}
        <div className="fvr-col">
          <div className="fvr-col-label">
            <span className="fvr-live-pill">
              <span className="fvr-live-dot" />
              LIVE
            </span>
            {elapsed != null ? <span>{elapsed}&prime;</span> : null}
          </div>
          <div className="fvr-score-line">{scoreline}</div>
          <div className="fvr-leader">{leaderLabel}</div>

          {/* AI live read */}
          {liveRead ? (
            <div className="fvr-ai-read">
              <span className="fvr-ai-marker" aria-hidden="true">💬</span>
              <span>{liveRead}</span>
            </div>
          ) : null}

          {/* LIVE STATS — bottom-aligned via margin-top:auto */}
          {hasLiveStats && (
            <div className="fvr-stats-block">
              <div className="fvr-stats-caption">Live stats</div>
              {possStat && (
                <SignalRow
                  homeText={possStat.home}
                  awayText={possStat.away}
                  label="Possession %"
                  homeVal={parseStatNum(possStat.home)}
                  awayVal={parseStatNum(possStat.away)}
                />
              )}
              {shotsStat && (
                <SignalRow
                  homeText={shotsStat.home}
                  awayText={shotsStat.away}
                  label="Shots"
                  homeVal={parseStatNum(shotsStat.home)}
                  awayVal={parseStatNum(shotsStat.away)}
                />
              )}
              {xgStat && (
                <SignalRow
                  homeText={xgStat.home}
                  awayText={xgStat.away}
                  label="xG"
                  homeVal={parseStatNum(xgStat.home)}
                  awayVal={parseStatNum(xgStat.away)}
                />
              )}
            </div>
          )}
        </div>
      </div>

      {/* VERDICT bar */}
      <div
        className="fvr-verdict"
        style={{ background: tone.bg, color: tone.color, borderLeftColor: tone.border }}
        aria-live="polite"
      >
        <span className="fvr-verdict-icon" aria-hidden="true">{TONE_ICONS[v.tone]}</span>
        <span>
          <strong>{v.label}</strong>{" "}
          <span style={{ fontWeight: 500, opacity: 0.92 }}>{v.text}</span>
        </span>
      </div>
    </section>
  );
}
