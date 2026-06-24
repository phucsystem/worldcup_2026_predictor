import { describe, it, expect } from "vitest";
import { bannerOutcome, forecastSegments } from "./banner";
import type { Forecast } from "./match";

function forecast(partial: Partial<Forecast>): Forecast {
  return { home_pct: 0, draw_pct: 0, away_pct: 0, factors: [], ...partial };
}

describe("bannerOutcome", () => {
  it("emphasises the winner and shows W/L tags when final", () => {
    expect(bannerOutcome("final", 3, 1)).toEqual({ homeCls: "win", awayCls: "lose", showWL: true });
    expect(bannerOutcome("final", 1, 3)).toEqual({ homeCls: "lose", awayCls: "win", showWL: true });
  });

  it("emphasises the live leader but never shows W/L tags", () => {
    expect(bannerOutcome("live", 2, 1)).toEqual({ homeCls: "win", awayCls: "lose", showWL: false });
    expect(bannerOutcome("live", 0, 2)).toEqual({ homeCls: "lose", awayCls: "win", showWL: false });
  });

  it("gives no emphasis on a draw (live or final)", () => {
    expect(bannerOutcome("final", 2, 2)).toEqual({ homeCls: "", awayCls: "", showWL: true });
    expect(bannerOutcome("live", 1, 1)).toEqual({ homeCls: "", awayCls: "", showWL: false });
  });

  it("gives no emphasis and no tags on the preview variant", () => {
    expect(bannerOutcome("preview", 0, 0)).toEqual({ homeCls: "", awayCls: "", showWL: false });
  });
});

describe("forecastSegments", () => {
  it("returns null when there is no forecast", () => {
    expect(forecastSegments(null)).toBeNull();
    expect(forecastSegments(undefined)).toBeNull();
  });

  it("passes through a clean integer split", () => {
    expect(forecastSegments(forecast({ home_pct: 52, draw_pct: 27, away_pct: 21 }))).toEqual({
      homePct: 52,
      drawPct: 27,
      awayPct: 21,
    });
  });

  it("rounds fractional percentages to integers (summing to ~100)", () => {
    const seg = forecastSegments(forecast({ home_pct: 52.4, draw_pct: 27.3, away_pct: 20.3 }))!;
    expect(seg).toEqual({ homePct: 52, drawPct: 27, awayPct: 20 });
    expect(seg.homePct + seg.drawPct + seg.awayPct).toBeGreaterThanOrEqual(99);
    expect(seg.homePct + seg.drawPct + seg.awayPct).toBeLessThanOrEqual(100);
  });

  it("clamps missing/negative fields to 0", () => {
    expect(
      forecastSegments(forecast({ home_pct: -5, draw_pct: 27, away_pct: undefined as unknown as number })),
    ).toEqual({ homePct: 0, drawPct: 27, awayPct: 0 });
  });
});
