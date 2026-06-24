import { describe, it, expect } from "vitest";
import { groupedResultRows, resultRowsFromResults, resultsToChips } from "@/lib/results";
import type { GroupStandings, RecentResult, ResultItem } from "@/lib/api";

function r(partial: Partial<RecentResult>): RecentResult {
  return {
    outcome: "W",
    fixture_id: null,
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

function group(recent: Partial<RecentResult>[]): GroupStandings {
  return {
    group_name: "Group A",
    rows: [{ team: "Brazil", recent_results: recent.map(r) }],
  } as unknown as GroupStandings;
}

describe("groupedResultRows", () => {
  it("carries forecastCorrect through from the recent result", () => {
    const rows = groupedResultRows([
      group([
        { fixture_id: 1, kickoff_utc: "2026-06-12T18:00:00Z", forecast_correct: true },
        {
          fixture_id: 2,
          kickoff_utc: "2026-06-13T18:00:00Z",
          home_team: "France",
          away_team: "Poland",
          forecast_correct: false,
        },
      ]),
    ]);
    const byFixture = Object.fromEntries(rows.map((row) => [row.fixtureId, row.forecastCorrect]));
    expect(byFixture[1]).toBe(true);
    expect(byFixture[2]).toBe(false);
  });

  it("defaults forecastCorrect to null when the field is absent", () => {
    const [row] = groupedResultRows([
      group([{ fixture_id: 9, kickoff_utc: "2026-06-12T18:00:00Z" }]),
    ]);
    expect(row.forecastCorrect).toBeNull();
  });
});

function item(partial: Partial<ResultItem>): ResultItem {
  return {
    fixture_id: 1,
    home_team: "Brazil",
    away_team: "Serbia",
    home_score: 3,
    away_score: 1,
    kickoff_utc: "2026-06-12T18:00:00Z",
    group_name: "A",
    stage: "Group Stage - 1",
    forecast_correct: true,
    ...partial,
  };
}

describe("resultRowsFromResults", () => {
  it("maps fields and derives winner from the score", () => {
    const [row] = resultRowsFromResults([item({})]);
    expect(row.home).toBe("Brazil");
    expect(row.winner).toBe("home");
    expect(row.group).toBe("A");
    expect(row.forecastCorrect).toBe(true);
  });

  it("labels knockout matches by stage when group_name is null", () => {
    const [row] = resultRowsFromResults([
      item({ group_name: null, stage: "Round of 16" }),
    ]);
    expect(row.group).toBe("Round of 16");
  });

  it("sorts newest first and applies no limit", () => {
    const rows = resultRowsFromResults([
      item({ fixture_id: 1, kickoff_utc: "2026-06-12T18:00:00Z" }),
      item({ fixture_id: 2, kickoff_utc: "2026-06-20T18:00:00Z", away_team: "Poland" }),
      item({ fixture_id: 3, kickoff_utc: "2026-06-15T18:00:00Z", away_team: "Ghana" }),
    ]);
    expect(rows).toHaveLength(3);
    expect(rows.map((row) => row.fixtureId)).toEqual([2, 3, 1]);
  });

  it("skips items with missing teams or scores", () => {
    const rows = resultRowsFromResults([
      item({ home_score: null }),
      item({ away_team: null }),
    ]);
    expect(rows).toEqual([]);
  });

  it("draws when scores are level", () => {
    const [row] = resultRowsFromResults([item({ home_score: 2, away_score: 2 })]);
    expect(row.winner).toBe("draw");
  });
});
