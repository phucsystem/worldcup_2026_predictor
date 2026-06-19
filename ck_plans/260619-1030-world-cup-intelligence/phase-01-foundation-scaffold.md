---
phase: 1
title: "Foundation & Scaffold"
status: completed
priority: P1
effort: "1-2d"
dependencies: []
---

# Phase 1: Foundation & Scaffold

## Overview
Stand up the monorepo skeleton, local Postgres, DB schema migrations, and config plumbing so every later phase has a working dev loop.

## Requirements
- Functional: `docker-compose up` runs Postgres + a FastAPI health endpoint; migrations apply cleanly.
- Non-functional: reproducible local env, secrets via env vars (never committed), typed config.

## Architecture
Monorepo layout:
```
/backend     FastAPI app + pipeline + collector (Python, snake_case)
/frontend    Next.js (React + TS) + Tailwind
/infra       Azure Bicep / container config (later phases)
/db          Alembic migrations
docker-compose.yml   Postgres + backend for local dev
.env.example
```
- Backend deps via `uv` (or poetry): fastapi, uvicorn, sqlalchemy, alembic, psycopg, pydantic-settings, langgraph, langchain-openai (DeepSeek is OpenAI-compatible), httpx, pytest.
- Config: `pydantic-settings` reads `DATABASE_URL`, `API_FOOTBALL_KEY`, `DEEPSEEK_API_KEY`, `BRIEF_TIMEZONE`.

### DB schema (Alembic initial migration)
- `matches` (id PK, fixture_id unique, group, home_team, away_team, home_score, away_score, status, kickoff_utc, events_json JSONB, updated_at)
- `standings` (id PK, snapshot_date, group, team, played, won, drawn, lost, gf, ga, gd, points, position, prev_position, UNIQUE(snapshot_date, group, team))
- `articles` (id PK, brief_date unique, title, summary, body_md, status, model_used, created_at)
- `agent_runs` (id PK, run_id, brief_date, started_at, finished_at, node_timings JSONB, tokens_in, tokens_out, cost_usd, status, error)

## Related Code Files
- Create: `docker-compose.yml`, `.env.example`, `backend/pyproject.toml`, `backend/app/main.py` (health), `backend/app/config.py`, `backend/db/alembic.ini`, `backend/db/migrations/0001_initial.py`, `frontend/` (Next.js TS scaffold via create-next-app), `README.md`
- Modify: —
- Delete: —

## Implementation Steps
1. Init backend with `uv`; add deps; `backend/app/config.py` via pydantic-settings.
2. `backend/app/main.py` with `GET /health`.
3. Configure Alembic; write `0001_initial` migration for the 4 tables above.
4. `docker-compose.yml`: postgres:16 service + backend service; healthchecks; volume for pgdata.
5. Scaffold `frontend/` with `create-next-app --typescript --tailwind --app`.
6. `.env.example` with all required keys; `README.md` dev-loop instructions.

## Success Criteria
- [x] `docker-compose up` → Postgres healthy + `GET /health` returns 200.
- [x] `alembic upgrade head` creates all 4 tables.
- [x] `frontend` dev server renders default page.
- [x] No secrets committed; `.env` gitignored.

## Risk Assessment
- Python tooling drift (uv vs poetry) → pick `uv`, pin versions. Low risk.
- Alembic + JSONB column types → verify psycopg3 dialect. Low.
