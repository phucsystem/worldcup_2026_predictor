---
phase: 1
title: Data & collector
status: completed
priority: P1
dependencies: []
effort: ''
---

# Phase 1: Data & collector

## Overview

Add storage for match statistics and the verdict to the `matches` table, add a
collector call for `/fixtures/statistics`, and extend the guarded once-only
on-finish backfill to fetch + persist statistics for newly-finished matches.

## Requirements

- Functional: persist raw statistics JSON + verdict text/model per match; fetch
  statistics from API-Football; backfill stats for finished matches exactly once.
- Non-functional: a failed statistics fetch must never abort the collect (log +
  skip, matching `backfill_finished_events`).

## Architecture

- New nullable columns on `matches_table` (`repository.py:15`):
  `statistics_json` (`sa.JSON`), `verdict_text` (`sa.Text`/`sa.String`),
  `verdict_model` (`sa.String`). Alembic migration `0007` (down_revision `0006`).
- `APIFootballClient.get_fixture_statistics(fixture_id)` → `_get("/fixtures/statistics", {"fixture": fixture_id})`,
  returns the raw `response` list (per-team stat arrays). Mirrors `get_events` (`:224`).
- Extend `backfill_finished_events` (or add a sibling `backfill_finished_statistics`
  invoked from the same block in `collect.run`, `:124-129`) to fetch stats for
  finished matches whose `statistics_json` is null, set `m.statistics`, persist.
  Reuse the `select_fixtures_needing_*` guard shape so stats are fetched once.
- Verdict population is wired here as a no-op hook point; the generation itself
  lands in Phase 2 (keeps the LLM dependency out of the data layer).

## Related Code Files
- Modify: `backend/app/data/repository.py` (3 columns on `matches_table`)
- Create: `backend/db/migrations/versions/0007_match_statistics_and_verdict.py`
- Modify: `backend/app/data/api_football.py` (`get_fixture_statistics`)
- Modify: `backend/app/data/collect.py` (stats backfill in the on-finish block)
- Modify/Create: `backend/app/api/fixtures.py` (`select_fixtures_needing_statistics` guard, beside `select_fixtures_needing_events`)
- Create/Modify tests: `backend/tests/test_match_statistics.py`

## Implementation Steps

1. **(TDD)** Write `select_fixtures_needing_statistics(matches, existing)` test:
   returns only finished fixture ids absent from `existing`; preview/live skipped.
2. **(TDD)** Write a `get_fixture_statistics` test against a captured/stubbed
   API-Football statistics payload (assert it returns the raw response list).
3. Add the three nullable columns to `matches_table`; write Alembic `0007`
   (`op.add_column` × 3; downgrade drops them).
4. Implement `get_fixture_statistics` and `select_fixtures_needing_statistics`.
5. Extend the `collect.run` on-finish block to backfill statistics (guarded,
   wrapped in try/except → `log.warning` + continue, like events).
6. Run migration locally; run `pytest`.

## Success Criteria
- [ ] Migration `0007` applies and reverts cleanly; `matches` gains the 3 columns.
- [ ] `get_fixture_statistics` returns the raw statistics response; unit-tested.
- [ ] `select_fixtures_needing_statistics` guards to finished + un-backfilled; unit-tested.
- [ ] A failing stats fetch logs and is skipped without aborting the collect.
- [ ] `pytest` passes (new tests written before implementation).

## Risk Assessment
- Stats payload shape varies per provider/season — keep this layer raw
  (store the response as-is); all interpretation happens in Phase 3 shaping so it
  stays pure/testable. Verify one real response shape before finalizing the test fixture.
