---
phase: 1
title: "Backend Data Backing"
status: complete
priority: P1
effort: "0.5d"
dependencies: []
---

# Phase 1: Backend Data Backing

## Overview
Expose the data the prototype-only UI elements need, derived from existing tables (no migration). Verification (2026-06-20) corrected the data model: **Sparkline and ResultChip are both recent-form views** — driven by one feed of recent finished matches per team. A standings **trend** endpoint is also built per user decision, but has no prototype UI consumer. Tests-first (pytest exists).

## Requirements
- **Functional:**
  - Add `recent_results: list[RecentResult]` to each `StandingRow` in `GET /api/standings`, where `RecentResult = {outcome: "W"|"D"|"L", home_team, away_team, home_score, away_score, kickoff_utc}`. Up to **5** most-recent finished matches for that team. Powers BOTH ResultChip (renders the match) and Sparkline (reads the `outcome` sequence).
  - Build `GET /api/standings/trend?team=<name>&window=<N>` (default N=5) → ordered `{snapshot_date, position, points}` series from historical snapshots. **Standalone — no prototype element consumes it; not on the parity critical path.**
- **Non-functional:**
  - **Finished = strict set** `{"FT","AET","PEN"}` only; in-play (1H/HT/2H/LIVE) and `_NOT_STARTED` excluded.
  - **Graceful degrade:** thin data → empty list, never an error, never fabricated.
  - Batch queries (one finished-matches query, grouped by team — no per-team round-trips). No new deps, no migration.

## Architecture
- **Recent results (primary):** batch-query `matches` where `status in {"FT","AET","PEN"}`, ordered by `kickoff_utc`; group by team (a match attaches to both its home and away team). Per team take last 5. Pure helper `match_outcome(team, match) -> "W"|"D"|"L"` (compare scores from team's perspective) keeps outcome logic DB-free and unit-testable. Attach during the existing standings assembly loop.
  - **Join is safe:** `standings.team` and `matches.home_team/away_team` both originate from API-Football `.name` (verified `api_football.py:94-113`), so exact-match keys align.
  - Centralize `_FINISHED = {"FT","AET","PEN"}` (mirror of the existing `_NOT_STARTED` set in `api_football.py`).
- **Trend (secondary):** query `standings_table` by team, order by `snapshot_date`, take last N → `{snapshot_date, position, points}`. Reuse `_get_session()`.

## Related Code Files
- Modify: `backend/app/api/standings.py` (add `recent_results` + `RecentResult` model to standings; add trend endpoint; `_FINISHED` set)
- Modify: `backend/app/data/repository.py` (finished-matches query helper if needed)
- Reference: `backend/app/api/fixtures.py` (matches table access), `backend/app/data/api_football.py:15-16` (`_NOT_STARTED` convention), `backend/app/data/standings_math.py` (W/D/L conventions)
- Create: `backend/tests/test_recent_results.py`
- Create: `backend/tests/test_standings_trend.py`

## Implementation Steps
1. **(TEST FIRST)** `test_recent_results.py`: pure `match_outcome` — W/D/L from home & away perspective; assembly with **strict finished filter** (FT/AET/PEN included; NS/1H/HT excluded); ordering most-recent; >5 capped to 5; **0 finished → `[]`**; unknown team → `[]`.
2. Implement `match_outcome` (pure) + `_FINISHED`; wire batch finished-matches fetch + grouping into `get_standings` assembly; add `RecentResult` + `recent_results` to the response models.
3. **(TEST FIRST)** `test_standings_trend.py`: seed 3 snapshots → ordered window; window > available → what exists; no snapshots → `[]`; unknown team → `[]`.
4. Implement `GET /api/standings/trend`.
5. Run full backend suite; confirm no regression in the 6 existing test files.

## Success Criteria
- [ ] `test_recent_results.py` + `test_standings_trend.py` written before implementation, then passing.
- [ ] `recent_results` on every `StandingRow`: up to 5 finished matches with outcome + scoreline; `[]` when none.
- [ ] Only FT/AET/PEN counted; in-play matches excluded (asserted by test).
- [ ] `GET /api/standings/trend` returns ordered real series; `[]` when thin.
- [ ] All previously-passing backend tests still green.

## Risk Assessment
- **Trend endpoint is unused by UI** — keep it minimal; do not let it expand parity scope (user-requested extra). No frontend fetcher will be wired (no consumer).
- **Status code coverage** — confirm AET/PEN actually appear from the source for WC knockouts; if only FT is emitted pre-knockout, form still works (FT covers group stage). Mitigation: `_FINISHED` is a single set easy to extend.
- **Thin data now** — few finished matches early → short/empty `recent_results`; expected, handled by graceful degrade.
