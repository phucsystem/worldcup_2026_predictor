# Phase 7: Fixtures & Data Enrichment Implementation Complete

**Date**: 2026-06-20 10:34
**Severity**: Low
**Component**: Backend (API, database, collector)
**Status**: Code Complete — Live Data Deferred

## What Happened

Phase 7 delivered the backend for fixtures browsing, knockout bracket visualization, and "stars to watch" (top scorers), plus team logos across the standings. Committed as `ba976d1c` without pushing. All new endpoints verified 200 OK against empty DB; full test suite 46/46 green.

**Delivered artifacts:**
- Migration 0003: `teams` + `top_scorers` tables; added `matches.stage` column (persistence gap).
- Collector: `get_teams()` (logos from standings) + `get_top_scorers()` (1 extra API call, non-fatal); idempotent upserts.
- API: `/api/fixtures/upcoming` (day-grouped, `up_next` convenience), `/api/fixtures/knockout` (bracket by round), `/api/stars` (top scorers ordered by goals); additive `logo` on standings.
- Tests: 13 new pure shaping tests, zero mocks for grouping/bracket logic.

## The Brutal Truth

Phase 7 exposed a data-model gap that should have been caught during planning. The original acceptance criteria assumed `matches.stage` was queryable for the knockout bracket, but it was never persisted—only a model comment acknowledged "Not persisted." Discovery happened at implementation time: "Wait, how do I group knockout matches by round without `stage`?" This is a planning fail disguised as a backend requirement. The fix was straightforward (add column + upsert), but it's the kind of gotcha that wastes a sprint if discovered in Phase 8's frontend work.

Live data enrichment is deferred pending `API_FOOTBALL_KEY` + season 2022 (free-plan limitation repeats from Phases 2–3). The endpoints work, the schema is ready, but the success criteria "teams ~32 rows w/ logos, top scorers populated" can't be verified without external API access.

## Technical Details

**Stage persistence gap:**
- `matches.stage` (e.g., "Round of 16", "Final") arrived from `/fixtures` in Phase 2 but was never written to `matches.stage` column.
- Phase 7 added the column + upsert logic so `/api/fixtures/knockout` can group by stage→round.
- Verified migration reverses cleanly on local Postgres; schema change is non-breaking.

**API-call budget decision:**
- Original constraint: "≤1 extra API call per collect."
- Team logos already live in `team.logo` from the standings fetch (no extra call).
- Refactored `team_group_map()` → `get_teams()` to extract `{id, name, logo}` from existing standings payload, reusing the single `/standings` fetch.
- Top scorers uses exactly 1 new `/players/topscorers` call; logged and continues (non-fatal) on error.

**Data-integrity edge case caught in code review:**
- Missing API `id` would coalesce to key `0`, silently collapsing multiple rows (teams or players).
- Fix: skip rows without a valid id before upsert. Prevents data corruption during malformed API responses.

**Idempotence verified:**
- Teams: `team_id` PK + `ON CONFLICT DO UPDATE` (update `updated_at`).
- Top scorers: `UNIQUE(season, player_id)` + `ON CONFLICT DO UPDATE` (idempotent re-run safe).

## What We Tried

1. **Initial approach:** Query `matches.stage` directly on unsupported column → discovered column didn't exist.
2. **Fallback:** Check models.py → "Not persisted" comment. Added migration + upsert.
3. **Logo extraction:** Evaluated separate `/teams` endpoint → rejected (extra call). Extracted from standings response instead (verified in `api_football.py`).
4. **Top scorers error handling:** Made non-fatal (log + continue) so a missing plan/season never aborts a whole collect run.

## Root Cause Analysis

**Stage persistence gap:** Planning phase treated `matches.stage` as a given (Phase 2 fetch outputs it), but missed that "fetched" ≠ "persisted." No one walked the data pipeline end-to-end: API response → model → database column. A simple RACI checklist at planning time ("who confirms this lands in the schema?") would have caught it.

**Data-integrity edge case:** The model accepted any `id` value including missing/null, defaulting to `0`. Upsert logic didn't validate before insertion. Code review (not testing) caught it because the bug only manifests with malformed external data.

**Live data deferral:** Repeats earlier dependency: free-plan `API_FOOTBALL_KEY` blocks 2026 season; 2022 is the demo vehicle. This is a known trade-off, not a failure—documented in planning.

## Lessons Learned

1. **Schema persistence isn't automatic.** When planning phases depend on data from earlier phases, explicitly confirm the data is *persisted* in the target table, not just fetched. Add a schema-review step to planning.
2. **API-call budgets drive architecture decisions.** Reusing an existing fetch (standings → logos) forced a cleaner extraction helper and avoided bloat. Worth documenting the constraint up front.
3. **Non-fatal error handling for auxiliary data.** Top scorers is "nice to have"; teams is "required." Splitting error handling by criticality (fatal vs. logged) prevents one missing resource from cascading.
4. **Malformed external data is a real threat.** Unit tests can't catch this without fuzzing; code review found the `id=0` collapse. Consider defensive parsing (skip nulls) as default practice on external payloads.

## Next Steps

1. **Live enrichment:** Once an `API_FOOTBALL_KEY` is available, run a full collect on season 2022 to populate `teams` + `top_scorers`; verify `/api/fixtures/knockout` returns 16 matches as a bracket.
2. **Phase 8 consumes endpoints:** Build `/fixtures` page (day-grouped upcoming), knockout modal (bracket view), home enrichments (up_next, stars).
3. **2026 season unblock:** Evaluate paid API-Football plan or find alternative free source for real tournament data; document timeline.

**Status:** Code complete, pending live API key for data verification. All 46 tests passing. Ready for Phase 8 integration.
