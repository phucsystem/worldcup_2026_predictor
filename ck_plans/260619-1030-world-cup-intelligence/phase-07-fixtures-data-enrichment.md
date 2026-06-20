---
phase: 7
title: "Fixtures & Data Enrichment"
status: done (code complete; live enrichment needs API_FOOTBALL_KEY)
priority: P2
effort: "1-2d"
dependencies: [2, 4]
---

# Phase 7: Fixtures & Data Enrichment

## Overview
Add the data + read API needed for the two unbuilt prototype screens (Fixtures, Changelog) and the data-backed visual polish (team flags/logos, "Stars to watch"). All new numbers stay deterministic / sourced from the API; the LLM is not involved.

## Key Insights
- Team **logos** (national crests, usable as flags) are already present in the `/standings` response (`team.logo` URL) — **no extra API call**; extract during the existing collect.
- **Top scorers** are available on the free plan for season 2022 via `/players/topscorers` (verified: 20 players w/ photo URLs + goals, 1 call/run).
- **Knockout** matches already land in `matches` (group_name NULL, `stage` like "Round of 16" … "Final") from the full-season fetch added in Phase 2's collector — no new fetch needed for the bracket.
- External images come from `media.api-sports.io`; render via plain `<img>` + `onerror` fallback (Phase 8) — no `next.config` remote-host setup.

## Requirements
- Functional: an API exposes (a) upcoming fixtures grouped by day with kickoff times, (b) the knockout bracket, (c) tournament top scorers, and (d) team logos joinable to standings/fixtures rows.
- Non-functional: read-only; ≤1 extra API-Football call per collect (topscorers); idempotent upserts; degrades gracefully without an API key.

## Architecture
### DB (Alembic migration 0003)
- `teams` (team_id PK, name UNIQUE, logo_url, group_name nullable, updated_at)
- `top_scorers` (id PK, season, player_id, name, photo_url, team, goals, UNIQUE(season, player_id))

### Collector extensions (`backend/app/data/`)
- `api_football.py`: add `get_top_scorers()` (`/players/topscorers`) → list of small `TopScorer` models (player_id, name, photo_url, team, goals); extract `{id,name,logo}` per team from the standings response (new helper, reuse existing `get_standings` fetch — do not add calls for logos).
- `repository.py`: `upsert_teams(session, teams)` (key team_id), `upsert_top_scorers(session, season, rows)` (key season+player_id). Reuse the snapshot-replace pattern where appropriate.
- `collect.py`: during a run, upsert `teams` (from standings) and `top_scorers` (one extra call). Non-fatal if topscorers errors (log + continue).

### API (`backend/app/api/`)
- `fixtures.py` (new router):
  - `GET /api/fixtures/upcoming` → matches with no score and future `kickoff_utc`, grouped by day (date → list), each row enriched with home/away `logo`. Includes an `up_next` (soonest) convenience field.
  - `GET /api/fixtures/knockout` → matches with `stage` in the knockout set (group_name NULL), shaped as a bracket (round → ties), logos joined. Empty-state when none yet.
  - `GET /api/stars` → top scorers (name, team, goals, photo_url), ordered by goals.
- Enrich existing `standings.py` rows with a `logo` field (join `teams` by name). Keep response back-compatible (additive field).

## Related Code Files
- Create: `backend/db/migrations/versions/0003_teams_and_top_scorers.py`, `backend/app/api/fixtures.py`, `backend/tests/test_fixtures_shaping.py`
- Modify: `backend/app/data/api_football.py`, `backend/app/data/models.py` (add `TopScorer`, `Team`), `backend/app/data/repository.py`, `backend/app/data/collect.py`, `backend/app/api/standings.py` (logo field), `backend/app/main.py` (mount fixtures router)

## Implementation Steps
1. Migration 0003: `teams`, `top_scorers` tables.
2. Models: `Team`, `TopScorer`.
3. `api_football.py`: `get_top_scorers()` + team-logo extraction helper from standings payload.
4. `repository.py`: `upsert_teams`, `upsert_top_scorers`; standings query joins logo.
5. `collect.py`: upsert teams + top scorers (non-fatal on topscorers failure).
6. `fixtures.py`: upcoming + knockout + stars endpoints; mount in `main.py`.
7. Tests: pure shaping tests for upcoming grouping + knockout bracket assembly (no network).

## Todo List
- [x] Migration 0003 applies (teams, top_scorers; also adds `matches.stage`) — verified up/down on local PG
- [x] Collect upserts teams (logos) + top scorers; idempotent (topscorers non-fatal) — code complete; live run needs key
- [x] `/api/fixtures/upcoming`, `/api/fixtures/knockout`, `/api/stars` return correct JSON — 200 + shapes verified via TestClient
- [x] Standings rows carry `logo` (additive, back-compatible)
- [x] Shaping unit tests pass; graceful without API key — 13 new tests, 46/46 suite green

## Success Criteria
- [ ] After a collect (season 2022), `teams` ~32 rows w/ logos, `top_scorers` populated (Mbappé etc.). — **needs `API_FOOTBALL_KEY` + live collect**
- [ ] `/api/fixtures/knockout` returns the 16 knockout matches as a bracket; `/api/stars` returns scorers w/ photos. — **needs live collect** (endpoints + bracket shaping verified against empty DB)
- [x] No new write paths exposed publicly; read-only.
- [x] Re-running collect does not duplicate teams/scorers. — guaranteed by `team_id` PK + `UNIQUE(season, player_id)` + `ON CONFLICT DO UPDATE`

> **Implementation note:** `matches.stage` was not previously persisted; Phase 7 adds the column + persistence so the knockout endpoint can group matches by round. The `id`-missing edge (silent key collapse to 0) is guarded by skipping rows without a team/player id. Two data-dependent success criteria remain pending a live collect with an API key (same external-dependency deferral as Phases 2–3).

## Risk Assessment
- Topscorers adds 1 call/run → still well within 100/day. Non-fatal on error.
- 2026 season blocked on free plan (same as existing data) → real enrichment demoed on 2022; 2026 needs paid plan.
- Team-name join (standings.team ↔ teams.name) must use the exact API name strings (already consistent — verified in Phase "fix" work).

## Security Considerations
- External image URLs are stored as data only; sanitized/rendered safely in Phase 8 (`<img>` + fallback, no `innerHTML`).
- No secrets; topscorers uses the existing key.

## Next Steps
Phase 8 consumes these endpoints to build `/fixtures`, the home enhancements, and flags/logos across screens.
