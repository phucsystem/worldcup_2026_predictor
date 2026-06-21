import type { Forecast, Side } from "@/lib/match";
import { forecastOutcome } from "@/lib/match";
import TeamFlag from "@/components/team-flag";

interface Props {
  forecast: Forecast;
  homeTeam: string | null;
  awayTeam: string | null;
  homeLogo: string | null;
  awayLogo: string | null;
  homeScore: number | null;
  awayScore: number | null;
}

function sideName(side: Side, home: string | null, away: string | null): string {
  if (side === "home") return home ?? "Home";
  if (side === "away") return away ?? "Away";
  return "Draw";
}

// Finished-state conclusion: forecast pick vs actual result with an auto
// hit/miss badge. No prose — the comparison cells and badge tell the story.
export default function ForecastOutcome({
  forecast,
  homeTeam,
  awayTeam,
  homeLogo,
  awayLogo,
  homeScore,
  awayScore,
}: Props) {
  const outcome = forecastOutcome(forecast, homeScore, awayScore);
  if (!outcome) return null;

  const pct = Math.max(forecast.homePct, forecast.drawPct, forecast.awayPct);
  const predName = sideName(outcome.predictedSide, homeTeam, awayTeam);
  const predLogo =
    outcome.predictedSide === "home" ? homeLogo : outcome.predictedSide === "away" ? awayLogo : null;

  const actualText =
    outcome.actualSide === "draw"
      ? `Drew ${homeScore}–${awayScore}`
      : `${sideName(outcome.actualSide, homeTeam, awayTeam)} won ${Math.max(homeScore ?? 0, awayScore ?? 0)}–${Math.min(homeScore ?? 0, awayScore ?? 0)}`;
  const actualLogo =
    outcome.actualSide === "home" ? homeLogo : outcome.actualSide === "away" ? awayLogo : null;

  return (
    <div className={`fc-outcome ${outcome.hit ? "hit" : "miss"}`}>
      <div className="fc-outcome-head">
        <h3 className="fc-outcome-title">
          {outcome.hit ? "The forecast called it" : "The forecast missed"}
        </h3>
        <span className="fc-outcome-badge">{outcome.hit ? "✓ Forecast hit" : "✗ Forecast miss"}</span>
      </div>
      <p className="fc-note" style={{ marginTop: 0, marginBottom: "var(--space-3)" }}>
        Illustrative only — the pick above is the placeholder forecast, not a real model.
      </p>
      <div className="fc-compare">
        <div className="fc-compare-cell">
          <div className="fc-compare-label">Forecast</div>
          <div className="fc-compare-val">
            {outcome.predictedSide !== "draw" && <TeamFlag team={predName} logo={predLogo} size={20} />}
            {predName} · {pct}% most likely
          </div>
        </div>
        <div className="fc-compare-cell">
          <div className="fc-compare-label">Actual result</div>
          <div className="fc-compare-val">
            {outcome.actualSide !== "draw" && <TeamFlag team={sideName(outcome.actualSide, homeTeam, awayTeam)} logo={actualLogo} size={20} />}
            {actualText}
          </div>
        </div>
      </div>
    </div>
  );
}
