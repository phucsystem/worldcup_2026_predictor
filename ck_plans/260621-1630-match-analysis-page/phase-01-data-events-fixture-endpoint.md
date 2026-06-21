---
phase: 1
title: "Data: events + fixture endpoint"
status: complete
priority: P1
dependencies: []
effort: "M"
---

# Phase 1: Data — match events + single-fixture endpoint

## Overview

Populate `matches.events_json` from API-Football and expose `GET /api/fixtures/{fixture_id}` returning a `FixtureDetail` (existing `FixtureRow` fields + normalized `events`). This is the only real backend work; the column already exists, so no migration.

## Requirements

- Functional:
  - Events fetched and stored for matches that are live or finished, via the existing collection paths (no new scheduler).
  - New read-only endpoint `GET /api/fixtures/{fixture_id}` → `FixtureDetail` (FixtureRow + `events: list[MatchEvent]`); 404 when the id is unknown.
  - Events normalized into a stable, frontend-friendly shape (minute, type, detail, player, team side) via a pure function.
- Non-functional:
  - No extra API-Football calls on the daily path beyond live/finished fixtures (bounded; respect rate limits).
  - Shaping logic in pure functions (no DB/network) so it is unit-testable, matching `api/fixtures.py` convention.

## Architecture

**Event normalization (pure):** add `normalize_events(raw: list[dict], home_team: str, away_team: str) -> list[MatchEvent]` in `api/fixtures.py` (or a sibling `app/data/events.py`). Maps raw API-Football events to:

```
MatchEvent: { minute:int, extra:int|None, type:str ("Goal"|"Card"|"subst"|...),
              detail:str, player:str|None, assist:str|None,
              team:str|None, side:"home"|"away"|None }
```

`side` derived by matching event `team.name` to home/away team name. Running score is NOT computed here (the timeline running score is derived frontend-side in Phase 2 from goal events, keeping this function dumb).

**Population:**
- `collect_live()` (`collect.py:128`): for each in-play fixture it already upserts, call `client.get_events(fixture_id)` and include `events_json` in the upsert. Few concurrent live matches → cheap.
- `collect.run()` (`collect.py:39`): for fixtures whose `status` is finished AND whose stored `events_json` is empty, fetch + store once (backfill). Guard so finished matches aren't re-fetched every run — pure helper `select_fixtures_needing_events(matches, existing) -> list[int]`.
- `upsert_matches` must persist `events_json` when present without clobbering existing events with null (only overwrite when new events are non-empty).

**Endpoint:** add to `api/fixtures.py`:
```python
class FixtureDetail(FixtureRow):
    events: list[MatchEvent] = []

@router.get("/{fixture_id}", response_model=FixtureDetail)
def get_fixture(fixture_id: int): ...   # 404 via HTTPException if not found
```
Route ordering: ensure `/{fixture_id}` is registered after the static `/upcoming`, `/live`, `/knockout` paths so it doesn't shadow them (FastAPI matches by registration order for path params vs literals — verify with a test hitting `/upcoming`).

## Related Code Files

- Modify: `backend/app/api/fixtures.py` (add `MatchEvent`, `FixtureDetail`, `normalize_events`, `select_fixtures_needing_events`, `get_fixture` route)
- Modify: `backend/app/data/collect.py` (`collect_live` + `run` event population)
- Modify: `backend/app/data/repository.py` (`upsert_matches` to persist `events_json` without null-clobber)
- Create: `backend/tests/test_match_events.py`, `backend/tests/test_fixture_detail_endpoint.py`
- Reference: `backend/app/data/api_football.py:224` (`get_events`), `backend/tests/test_fixtures_shaping.py` (test style)

## Implementation Steps (TDD)

1. **Tests first** — `test_match_events.py`:
   - `normalize_events`: goal/card/subst mapping; `side` resolution home vs away; unknown team → `side=None`; empty/None input → `[]`; extra-time `minute`+`extra`.
   - `select_fixtures_needing_events`: finished + empty events → selected; finished + already-has-events → skipped; not-started → skipped.
2. **Tests first** — `test_fixture_detail_endpoint.py`: known id → 200 with `events`; unknown id → 404; confirm `/api/fixtures/upcoming` still resolves (no route shadowing).
3. Run tests → red.
4. Implement `MatchEvent`, `FixtureDetail`, `normalize_events`, `select_fixtures_needing_events`, and the `get_fixture` route.
5. Wire event population into `collect_live` and `run`; update `upsert_matches` null-clobber guard.
6. Run `cd backend && pytest` → green. Then full backend suite to catch regressions in fixtures/standings.

## Success Criteria

- [ ] `test_match_events.py` and `test_fixture_detail_endpoint.py` written first and pass.
- [ ] `GET /api/fixtures/{id}` returns `FixtureDetail` with normalized events; 404 on unknown id; existing fixture routes unaffected.
- [ ] `events_json` is populated for live + finished fixtures via existing collection paths; no re-fetch of already-stored finished events.
- [ ] Full backend `pytest` suite green.

## Risk Assessment

- **Touching the sync/collect path** could disrupt ingestion. Mitigation: event fetch is additive and guarded; failure to fetch events must not abort the match/standings upsert (wrap in try/except + log, consistent with existing `collect.run` error handling at `collect.py:96/104`).
- **Route shadowing** of `/{fixture_id}` over literals — covered by an explicit test.
- **Rate limits** on `get_events` — bounded to live + un-backfilled finished fixtures; log counts like the existing live refresh.
