import { describe, it, expect } from "vitest";
import {
  matchState,
  buildTimeline,
  goalscorers,
  forecastOutcome,
  placeholderForecast,
} from "./match";
import type { MatchEvent } from "./api";

function ev(partial: Partial<MatchEvent>): MatchEvent {
  return {
    minute: 0,
    extra: null,
    type: "Goal",
    detail: "Normal Goal",
    player: null,
    assist: null,
    team: null,
    side: null,
    ...partial,
  };
}

describe("matchState", () => {
  it("maps NS and unknown to preview", () => {
    expect(matchState("NS")).toBe("preview");
    expect(matchState("TBD")).toBe("preview");
    expect(matchState(null)).toBe("preview");
  });
  it("maps in-play codes to live", () => {
    for (const s of ["1H", "HT", "2H", "ET", "BT", "P", "LIVE"]) {
      expect(matchState(s)).toBe("live");
    }
  });
  it("maps finished codes to finished", () => {
    for (const s of ["FT", "AET", "PEN"]) {
      expect(matchState(s)).toBe("finished");
    }
  });
});

describe("buildTimeline", () => {
  it("computes a running score across multiple goals", () => {
    const events = [
      ev({ minute: 23, side: "away", player: "Mitrović" }),
      ev({ minute: 51, side: "home", player: "Vinícius" }),
      ev({ minute: 64, side: "home", player: "Rodrygo" }),
    ];
    const rows = buildTimeline(events);
    expect(rows.map((r) => r.score)).toEqual([
      { home: 0, away: 1 },
      { home: 1, away: 1 },
      { home: 2, away: 1 },
    ]);
  });

  it("credits the opponent for an own goal", () => {
    const events = [
      ev({ minute: 30, side: "home", detail: "Own Goal", player: "Defender" }),
    ];
    const rows = buildTimeline(events);
    expect(rows[0].score).toEqual({ home: 0, away: 1 });
  });

  it("non-goal events carry no score and do not change the running total", () => {
    const events = [
      ev({ minute: 20, side: "home", player: "A" }),
      ev({ minute: 39, type: "Card", detail: "Yellow Card", side: "away", player: "B" }),
      ev({ minute: 70, type: "subst", detail: "Substitution 1", side: "home", player: "C" }),
    ];
    const rows = buildTimeline(events);
    expect(rows[1].score).toBeNull();
    expect(rows[2].score).toBeNull();
    expect(rows[0].score).toEqual({ home: 1, away: 0 });
  });

  it("orders by minute then extra", () => {
    const events = [
      ev({ minute: 90, extra: 3, side: "home", player: "Late" }),
      ev({ minute: 90, extra: null, side: "away", player: "First" }),
      ev({ minute: 45, side: "home", player: "Early" }),
    ];
    const rows = buildTimeline(events);
    expect(rows.map((r) => r.player)).toEqual(["Early", "First", "Late"]);
  });
});

describe("goalscorers", () => {
  it("groups a player's two goals into one entry with both minutes", () => {
    const events = [
      ev({ minute: 51, side: "home", player: "Vinícius" }),
      ev({ minute: 78, side: "home", player: "Vinícius" }),
    ];
    const out = goalscorers(events);
    expect(out).toEqual([{ side: "home", player: "Vinícius", minutes: [51, 78] }]);
  });

  it("splits by side and ignores non-goal events", () => {
    const events = [
      ev({ minute: 23, side: "away", player: "Mitrović" }),
      ev({ minute: 64, side: "home", player: "Rodrygo" }),
      ev({ minute: 39, type: "Card", detail: "Yellow Card", side: "home", player: "X" }),
    ];
    const out = goalscorers(events);
    expect(out).toContainEqual({ side: "away", player: "Mitrović", minutes: [23] });
    expect(out).toContainEqual({ side: "home", player: "Rodrygo", minutes: [64] });
    expect(out).toHaveLength(2);
  });
});

describe("forecastOutcome", () => {
  const fc = placeholderForecast("Brazil", "Serbia"); // home favourite

  it("home favourite + home win → hit", () => {
    const out = forecastOutcome(fc, 3, 1);
    expect(out).toEqual({ hit: true, predictedSide: "home", actualSide: "home" });
  });

  it("home favourite + draw → miss", () => {
    const out = forecastOutcome(fc, 1, 1);
    expect(out).toEqual({ hit: false, predictedSide: "home", actualSide: "draw" });
  });

  it("returns null when scores are absent", () => {
    expect(forecastOutcome(fc, null, 1)).toBeNull();
    expect(forecastOutcome(fc, 2, null)).toBeNull();
  });
});

describe("placeholderForecast", () => {
  it("percentages sum to 100 and home is the most likely", () => {
    const fc = placeholderForecast("Brazil", "Serbia");
    expect(fc.homePct + fc.drawPct + fc.awayPct).toBe(100);
    expect(fc.homePct).toBeGreaterThan(fc.awayPct);
    expect(fc.factors.length).toBeGreaterThan(0);
    expect(fc.note).toMatch(/not produced by any model/i);
  });
});
