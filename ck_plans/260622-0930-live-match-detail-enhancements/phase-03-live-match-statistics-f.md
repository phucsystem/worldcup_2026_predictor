---
phase: 3
title: Live Match Statistics (F)
status: completed
priority: P2
dependencies: []
---

# Phase 3: Live Match Statistics (F)

## Overview

Show match statistics (possession, shots, shots on target, xG, corners) while a match is in play, refreshing on each live poll. The only item touching the backend poller: add a per-fixture `get_fixture_statistics` call to `collect_live`. Frontend is a straight reuse of the existing `MatchStats` component.

## Requirements

- Functional: `collect_live` fetches statistics for each in-play fixture and stores to `statistics_json`, overwriting on every poll (live, not once-only). The live match page renders a stats panel that updates with the 30s poll.
- Non-functional: a statistics-fetch failure for one fixture must never abort the score/status/events upsert (same per-fixture guard as the events fetch). No standings recompute, no LLM. Only fires while a fixture is in the kickoff window.

## Architecture

`collect_live` already loops in-play fixtures and, per fixture, fetches events under a try/except before a single `upsert_matches`. Add a sibling `get_fixture_statistics` call in the same loop, assigning `m.statistics`. `upsert_matches` already persists `statistics_json` (used by the finished-match backfill). `GET /api/fixtures/{id}` already serves `statistics` via `normalize_statistics`, and `FixtureDetail.statistics: MatchStat[]` already exists frontend-side. `match-live.tsx` currently omits stats; add the existing `<MatchStats>` (as used in `app/match/[fixture_id]/page.tsx:101`).

### Live → FT handoff (intended, do not fight)

Once the live poll has stored stats, `backfill_finished_statistics` skips that fixture (guarded on "has stats"). Final stored stats = the last live poll's. Acceptable — note it, don't add reconciliation.

## Related Code Files

- Modify: `backend/app/data/collect.py` — add guarded `get_fixture_statistics` fetch to `collect_live`'s per-fixture loop.
- Modify: `backend/tests/test_*.py` (new or existing collect test) — TDD for the stats path.
- Reference (do not change): `backend/app/data/api_football.py` (`get_fixture_statistics`), `backend/app/api/fixtures.py` (`normalize_statistics`, `MatchStat`), `backend/app/data/collect.py` (`backfill_finished_statistics` guard behavior).
- Modify: `frontend/components/match-live.tsx` — render `<MatchStats stats={fixture.statistics} ... />` when `fixture.statistics.length > 0`.
- Reference (do not change): `frontend/components/match-stats.tsx`, `frontend/lib/api.ts` (`FixtureDetail.statistics`).

## Implementation Steps

1. **(TDD) Write the backend test first** (mirror `test_match_events.py` style — fake client, in-memory/SQLite session factory or the existing collect test harness):
   - `collect_live` stores `statistics_json` for an in-play fixture the client returns stats for.
   - A second poll **overwrites** the stored stats (no once-only guard for live).
   - A `get_fixture_statistics` exception for one fixture is swallowed and the score/status/events upsert still succeeds (assert the match row still updated).
   - Fixtures not in our known set are still ignored (existing behavior preserved).
2. **Implement in `collect_live`:** inside the existing `for m in ours` loop, after the events fetch, add:
   ```python
   try:
       m.statistics = client.get_fixture_statistics(m.fixture_id) or None
   except Exception as exc:
       log.warning("Live statistics fetch failed for %s: %s", m.fixture_id, exc)
   ```
   Keep it inside the same try-guarded per-fixture block discipline as events (independent try so a stats failure doesn't drop events). Run backend tests → green.
3. **Frontend render:** in `match-live.tsx`, add a stats section (reuse `MatchStats`) below the timeline/goalscorers block, conditional on `fixture.statistics.length > 0`, with a "Match stats" section title consistent with the finished view.
4. **Verify:** backend `pytest`; frontend vitest + match-page e2e. If a live match is available, sanity-check that stats appear and refresh; otherwise rely on the unit tests + a seeded fixture.

## Success Criteria

- [ ] Backend test proves: stats stored for in-play fixture, overwritten on re-poll, and a stats-fetch exception does not abort the score/events upsert.
- [ ] `collect_live` adds the guarded statistics fetch without changing standings/LLM behavior.
- [ ] Live match page renders a stats panel that updates on the poll; hidden when no stats yet.
- [ ] FT handoff leaves stored stats intact (no double-fetch, no overwrite war) — verified by the existing backfill guard.

## Risk Assessment

- **Extra API call per in-play fixture per poll** → accepted (latency/cost deprioritized); bounded to the kickoff window and the small in-play set.
- **Partial stats early in a match** (xG/shots absent) → `normalize_statistics` already omits absent types (no zero-fill); panel simply shows fewer bars.
- **Stats fetch slow/timeout** → per-fixture try/except keeps the loop and the score upsert alive; next poll retries.
