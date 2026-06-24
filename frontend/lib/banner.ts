import type { Forecast } from "./match";

export type BannerVariant = "preview" | "live" | "final";

export interface BannerOutcome {
  homeCls: "" | "win" | "lose";
  awayCls: "" | "win" | "lose";
  showWL: boolean;
}

// Decides the winner/leader emphasis for the hero. The leading side is
// highlighted on both live and finished matches; the explicit W/L letter tags
// appear only once the result is final (a live lead is not yet a result).
export function bannerOutcome(variant: BannerVariant, hs: number, as: number): BannerOutcome {
  const showOutcome = variant === "live" || variant === "final";
  const homeLead = showOutcome && hs > as;
  const awayLead = showOutcome && as > hs;
  return {
    homeCls: homeLead ? "win" : awayLead ? "lose" : "",
    awayCls: awayLead ? "win" : homeLead ? "lose" : "",
    showWL: variant === "final",
  };
}

export interface ForecastSegments {
  homePct: number;
  drawPct: number;
  awayPct: number;
}

// Normalises a Forecast into the three integer percentages the hero bar renders.
// Returns null when there is no forecast so callers can omit the bar entirely.
export function forecastSegments(forecast: Forecast | null | undefined): ForecastSegments | null {
  if (!forecast) return null;
  const pct = (n: number | null | undefined) => Math.max(0, Math.round(n ?? 0));
  return {
    homePct: pct(forecast.home_pct),
    drawPct: pct(forecast.draw_pct),
    awayPct: pct(forecast.away_pct),
  };
}
