# Knockout bracket advances through extra time & penalties

**Date:** 2026-06-30 · **Branch:** feat/unlock-knockout-standings
**Plan:** `plans/260630-2101-knockout-extra-time-penalties/`

## Problem

Knockout ties level after 90/120 minutes produced no winner — the bracket stalled at
"TBD vs TBD" and the winner's path never highlighted. The root cause was a thin data model,
not hard logic: `_map_fixture` read only `goals` + `status` and discarded the fields
API-Football already returns — `score.penalty` and the `teams.{home,away}.winner` booleans
(set on the advancing side even for a penalty win). The old `_winner_team` comment ("not
derivable from the score") held only because the penalty data was never captured.

## Fix (Approach A — store the API's winner flag)

Three new `matches` columns: `winner_side` (`'home'|'away'|null`), `home_pen`, `away_pen`.

- Migration `0014` (down_revision `0013`) + `matches_table` Core def + `Match` model +
  `_map_fixture` capture (penalty score from `score.penalty`, `winner_side` from `teams.winner`).
- `_winner_team` / bracket advancement read `winner_side` first, falling back to the
  regulation score for decisive matches (back-compat); a level result with no `winner_side`
  still stays TBD rather than guess.
- Fields exposed on `FixtureRow`, `ResultItem`, `RecentResult` and threaded through every
  read/hydration path.
- Frontend `resolveWinner` / `finishedStatusLabel`: bracket highlights the advancing side and
  shows `(a.e.t.)` / penalty score; results + home widgets render `1-1 (a.e.t.) 4-3 pens`.

## What the review caught

The mandatory code-review flagged two real gaps the plan missed: the home-page "Latest
Results" widget (sourced from the standings `RecentResult` path, not `/api/results`) still
computed the winner by raw score and lacked the penalty fields — so a knockout PEN tie read
as a "draw"/"Full Time" on `/` while `/results` showed it correctly. `match_outcome` had the
same raw-score issue for the W/D/L form chips. Both fixed by extending `RecentResult` +
`recent_results_by_team` + `match_outcome` (prefer `winner_side`) and `groupedResultRows`.

## Decisions & notes

- **Live poller unchanged.** API-Football's `?live=all` drops finished matches, so the poller
  never sees the final shootout; the penalty/winner columns populate on the next daily collect
  re-fetch via `_map_fixture`. Bracket advancement after a shootout lags to that refresh —
  acceptable for this product.
- **Scope held to real results.** Forecast tie-breaks (predicting an advancer) were explicitly
  deferred; the AI-predicts-explicitly preference is recorded for a future round.

## Verification

Backend 411 pass, frontend 72 pass, tsc clean, migration `0013→0014` applies cleanly, seed
fixture verified (South Korea 1-1 Czechia, Czechia advance 4-3 on penalties). The Robot e2e
suite (penalty result on `/results`) runs in CI — not runnable locally without the full stack.
