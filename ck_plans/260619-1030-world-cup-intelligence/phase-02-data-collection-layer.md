---
phase: 2
title: "Data Collection Layer"
status: done
priority: P1
effort: "2-3d"
dependencies: [1]
---

# Phase 2: Data Collection Layer

## Overview
Fetch + normalize WC 2026 data from API-Football, persist to `matches`/`standings`, and compute all standings + qualification math deterministically in Python.

## Requirements
- Functional: a collector run populates `matches` (all completed to-date + upcoming) and a `standings` snapshot with correct points/GD/position deltas + qualification flags. Briefs cover the **full tournament-to-date**, so the collector exposes complete to-date facts each run. <!-- Updated: Validation Session 1 - coverage = full tournament-to-date -->
- Functional: initial backfill loads matches/standings from June 11 forward.
- Non-functional: data-source swappable behind one interface; standings math fully unit-tested; resilient to API gaps (missing scores, postponed).

## Architecture
- `DataSource` ABC: `get_fixtures(date_range)`, `get_standings()`, `get_events(fixture_id)`. One impl now: `APIFootballClient` (httpx, WC league/season params, 100 req/day budget).
- `football-data.org` fallback documented but **not implemented** (KISS).
- Normalization → internal pydantic models (`Match`, `StandingRow`).
- **Deterministic compute module** (`standings_math.py`, pure functions):
  - points = 3W+1D; GD; sort by points→GD→GF (WC tiebreak order).
  - `position` + `prev_position` (delta vs last snapshot).
  - qualification flags: top-2 per group + best-thirds logic (WC 2026 = 12 groups of 4, top 2 + 8 best thirds advance). Pure function over standings; no LLM.
- Seed `groups`/schedule once from `openfootball/worldcup.json` (static, no key) so site has structure pre-first-run.
- **Backfill from June 11** (tournament start): on initial setup, fetch + persist all completed `matches` and a current `standings` snapshot so tables are correct from day one. Briefs are forward-only (no back-briefs). <!-- Updated: Validation Session 1 - backfill = seed data, no back-briefs -->
- Persistence: upsert by natural keys (fixture_id; snapshot_date+group+team).

## Related Code Files
- Create: `backend/app/data/source.py` (ABC), `backend/app/data/api_football.py`, `backend/app/data/models.py`, `backend/app/data/standings_math.py`, `backend/app/data/seed_openfootball.py`, `backend/app/data/repository.py`, `backend/tests/test_standings_math.py`
- Modify: `backend/app/config.py` (API-Football base URL/key)

## Implementation Steps
1. Define `DataSource` ABC + pydantic `Match`/`StandingRow` models.
2. `APIFootballClient`: fixtures, standings, events for WC league+season; map raw JSON → models; handle missing/postponed.
3. `standings_math.py`: pure functions for points/GD/sort/position-delta/qualification (12×4, best-thirds). Unit tests with fixture tables incl. tie edge cases.
4. `repository.py`: idempotent upserts to `matches`/`standings`.
5. `seed_openfootball.py`: one-off seed of groups + schedule.
6. CLI: `python -m app.data.collect --date YYYY-MM-DD`.

## Success Criteria
- [ ] Collector run populates `matches` + a `standings` snapshot for a date.
- [ ] `test_standings_math` passes incl. tie-break + best-thirds edge cases.
- [ ] Re-running same date does not duplicate rows (idempotent upsert).
- [ ] API failure degrades gracefully (logs, partial-safe).

## Risk Assessment
- **API-Football free tier blocks current WC season** → fallback to football-data.org behind `DataSource`. Verify early in this phase.
- Best-thirds ranking is fiddly → cover with explicit unit tests; this is the correctness core.
- Rate limit (100/day) → batch calls per run (<10); cache within a run.
