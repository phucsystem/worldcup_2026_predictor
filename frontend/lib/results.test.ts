import { describe, it, expect } from "vitest";
import { resultsToChips } from "@/lib/results";
import type { RecentResult } from "@/lib/api";

function r(partial: Partial<RecentResult>): RecentResult {
  return {
    outcome: "W",
    home_team: "Brazil",
    away_team: "Serbia",
    home_score: 3,
    away_score: 1,
    kickoff_utc: "2026-06-12T18:00:00Z",
    ...partial,
  };
}

describe("resultsToChips", () => {
  it("maps each outcome to its variant + letter", () => {
    const out = resultsToChips([
      r({ outcome: "W" }),
      r({ outcome: "D" }),
      r({ outcome: "L" }),
    ]);
    expect(out.map((c) => c.variant)).toEqual(["win", "draw", "loss"]);
    expect(out.map((c) => c.letter)).toEqual(["W", "D", "L"]);
  });

  it("builds an abbreviated scoreline label", () => {
    const [chip] = resultsToChips([r({})]);
    expect(chip.label).toBe("BRA 3–1 SER");
  });

  it("returns [] for no results", () => {
    expect(resultsToChips([])).toEqual([]);
  });

  it("degrades gracefully on missing fields", () => {
    const [chip] = resultsToChips([
      r({ home_team: null, away_team: null, home_score: null, away_score: null }),
    ]);
    expect(chip.label).toBe("— ?–? —");
  });

  it("produces stable unique keys", () => {
    const out = resultsToChips([
      r({ kickoff_utc: "2026-06-12T18:00:00Z" }),
      r({ kickoff_utc: "2026-06-15T18:00:00Z" }),
    ]);
    expect(new Set(out.map((c) => c.key)).size).toBe(2);
  });
});
