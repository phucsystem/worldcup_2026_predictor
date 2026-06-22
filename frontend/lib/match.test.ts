import { describe, it, expect } from "vitest";
import {
  matchState,
  buildTimeline,
  goalscorers,
  subOnOff,
  eventKey,
  freshEventKeys,
  forecastOutcome,
} from "./match";
import type { Forecast } from "./match";
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

  it("carries the assister on goal rows", () => {
    const rows = buildTimeline([
      ev({ minute: 51, side: "home", player: "Vinícius", assist: "Rodrygo" }),
      ev({ minute: 64, type: "Card", detail: "Yellow Card", side: "away", player: "X", assist: null }),
    ]);
    expect(rows[0].assist).toBe("Rodrygo");
    expect(rows[1].assist).toBeNull();
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
    expect(out).toEqual([
      {
        side: "home",
        player: "Vinícius",
        minutes: [51, 78],
        goals: [
          { minute: 51, detail: "Normal Goal", assist: null },
          { minute: 78, detail: "Normal Goal", assist: null },
        ],
      },
    ]);
  });

  it("splits by side and ignores non-goal events", () => {
    const events = [
      ev({ minute: 23, side: "away", player: "Mitrović" }),
      ev({ minute: 64, side: "home", player: "Rodrygo" }),
      ev({ minute: 39, type: "Card", detail: "Yellow Card", side: "home", player: "X" }),
    ];
    const out = goalscorers(events);
    expect(out).toContainEqual({
      side: "away",
      player: "Mitrović",
      minutes: [23],
      goals: [{ minute: 23, detail: "Normal Goal", assist: null }],
    });
    expect(out).toContainEqual({
      side: "home",
      player: "Rodrygo",
      minutes: [64],
      goals: [{ minute: 64, detail: "Normal Goal", assist: null }],
    });
    expect(out).toHaveLength(2);
  });
});

describe("subOnOff", () => {
  it("maps player to on and assist to off (API-Football subst convention)", () => {
    const e = ev({ type: "subst", detail: "Substitution 1", side: "home", player: "Sub In", assist: "Sub Out" });
    expect(subOnOff(e)).toEqual({ on: "Sub In", off: "Sub Out" });
  });

  it("tolerates a missing player-off", () => {
    expect(subOnOff(ev({ type: "subst", player: "Sub In", assist: null }))).toEqual({
      on: "Sub In",
      off: null,
    });
  });
});

describe("eventKey / freshEventKeys", () => {
  it("eventKey is stable for identical events and distinct across minute/type/player/side", () => {
    const a = ev({ minute: 23, type: "Goal", player: "Mbappé", side: "home" });
    expect(eventKey(a)).toBe(eventKey(ev({ minute: 23, type: "Goal", player: "Mbappé", side: "home" })));
    expect(eventKey(ev({ minute: 24, type: "Goal", player: "Mbappé", side: "home" }))).not.toBe(eventKey(a));
    expect(eventKey(ev({ minute: 23, type: "Card", player: "Mbappé", side: "home" }))).not.toBe(eventKey(a));
    expect(eventKey(ev({ minute: 23, type: "Goal", player: "Other", side: "home" }))).not.toBe(eventKey(a));
    expect(eventKey(ev({ minute: 23, type: "Goal", player: "Mbappé", side: "away" }))).not.toBe(eventKey(a));
  });

  it("distinguishes same-minute events by extra time", () => {
    const base = ev({ minute: 90, player: "A", side: "home" });
    expect(eventKey({ ...base, extra: 3 })).not.toBe(eventKey(base));
  });

  it("distinguishes player-less events at the same minute by detail", () => {
    // two VAR rulings in the same minute, no player — must not collide
    const a = ev({ minute: 55, type: "Var", detail: "Goal cancelled", player: null, side: "home" });
    const b = ev({ minute: 55, type: "Var", detail: "Penalty confirmed", player: null, side: "home" });
    expect(eventKey(a)).not.toBe(eventKey(b));
  });

  it("freshEventKeys returns only keys absent from prev", () => {
    const g1 = ev({ minute: 23, player: "A", side: "home" });
    const g2 = ev({ minute: 51, player: "B", side: "away" });
    expect(freshEventKeys(new Set([eventKey(g1)]), [g1, g2])).toEqual([eventKey(g2)]);
  });

  it("returns [] when nothing is new or input is empty", () => {
    const g1 = ev({ minute: 10, player: "A", side: "home" });
    expect(freshEventKeys(new Set([eventKey(g1)]), [g1])).toEqual([]);
    expect(freshEventKeys(new Set(), [])).toEqual([]);
  });
});

describe("forecastOutcome", () => {
  const fc: Forecast = { home_pct: 64, draw_pct: 22, away_pct: 14, factors: [] }; // home favourite

  it("home favourite + home win → hit", () => {
    const out = forecastOutcome(fc, 3, 1);
    expect(out).toEqual({ hit: true, predictedSide: "home", actualSide: "home" });
  });

  it("home favourite + draw → miss", () => {
    const out = forecastOutcome(fc, 1, 1);
    expect(out).toEqual({ hit: false, predictedSide: "home", actualSide: "draw" });
  });

  it("away favourite + away win → hit", () => {
    const away: Forecast = { home_pct: 18, draw_pct: 24, away_pct: 58, factors: [] };
    const out = forecastOutcome(away, 0, 2);
    expect(out).toEqual({ hit: true, predictedSide: "away", actualSide: "away" });
  });

  it("returns null when scores are absent", () => {
    expect(forecastOutcome(fc, null, 1)).toBeNull();
    expect(forecastOutcome(fc, 2, null)).toBeNull();
  });
});
