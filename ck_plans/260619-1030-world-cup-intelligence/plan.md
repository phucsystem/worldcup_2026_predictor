---
title: "World Cup Intelligence — Daily AI Tournament Brief"
status: implemented
created: 2026-06-19
source: ck_plans/reports/brainstorm-design-260619-1018-world-cup-intelligence-report.md
blockedBy: []
blocks: []
---

# World Cup Intelligence — Implementation Plan

AI pipeline that auto-monitors FIFA WC 2026 and publishes a daily brief at 7:00 AM (Australia/Melbourne). Greenfield monorepo on Azure.

## Stack (locked)
- **Frontend:** Next.js (React + TypeScript) + Tailwind, SSR Container App
- **Backend:** FastAPI + LangGraph (3-node pipeline) + DeepSeek
- **Data:** API-Football free tier (football-data.org documented fallback)
- **DB:** PostgreSQL (Azure Flexible Server in prod, docker locally)
- **Infra:** Azure Container Apps (API + Next.js) + Container Apps Job (cron)

## Non-negotiable correctness rule
All standings / qualification arithmetic computed **in Python** (deterministic, unit-tested). LLM **narrates only** — never does table math.

## Phases

| # | Phase | Status | Depends on |
|---|-------|--------|-----------|
| 1 | [Foundation & Scaffold](phase-01-foundation-scaffold.md) | ✅ done | — |
| 2 | [Data Collection Layer](phase-02-data-collection-layer.md) | ✅ done | 1 |
| 3 | [LangGraph Agent Pipeline](phase-03-langgraph-agent-pipeline.md) | ✅ done (live run needs DEEPSEEK_API_KEY) | 2 |
| 4 | [Backend API & Frontend Slice](phase-04-backend-api-frontend-slice.md) | ✅ done | 3 |
| 5 | [Scheduling & Reliability](phase-05-scheduling-reliability.md) | ✅ done | 3, 4 |
| 6 | [Frontend Polish & Azure Deploy](phase-06-frontend-polish-azure-deploy.md) | 🟡 code+IaC done, live Azure deploy pending (user creds) | 4, 5 |

## Execution strategy
Phases 1→4 = the **vertical slice** (manual-trigger brief end-to-end + visible on site). Phase 5 automates it. Phase 6 polishes + ships to Azure. Ship-fast: get a *correct brief* visible by end of Phase 4 before investing in automation/polish.

## Key dependencies
- API-Football API key (free tier) — needed Phase 2.
- DeepSeek API key — needed Phase 3.
- Azure subscription + resource group — needed Phase 6.

## Reference
Design doc: `ck_plans/reports/brainstorm-design-260619-1018-world-cup-intelligence-report.md`

## Validation Log

### Session 1 — 2026-06-19

**Verification Results**
- Claims checked: 0 | Verified: 0 | Failed: 0 | Unverified: 0
- Tier: Full (6 phases) — N/A: greenfield repo, all referenced files are to-be-created (verified repo empty). Nothing to grep.
- WC 2026 format (48 teams, 12 groups of 4, top-2 + 8 best-thirds → 32) confirmed as factual record, not a decision.

**Decisions confirmed**
1. **Coverage window = Full tournament-to-date.** Each daily brief re-summarizes the whole tournament so far (not just last 24h). Trade-off accepted: more repetitive briefs + longer LLM input; mitigated by DeepSeek's large cheap context. → Phases 2, 3.
2. **Backfill = seed data, no back-briefs.** Backfill `matches`/`standings` from June 11 so tables are correct day one; briefs generated forward-only. → Phases 2, 5.
3. **LLM = deepseek-chat (V3)** for both Analyst + Editor. Reasoner deferred to V2 prediction agent. → Phase 3 (already specified).
4. **Failure recovery = keep prior + log + manual re-trigger.** On failure, do not publish a broken brief; site keeps last *successful* brief; `agent_runs` logs failure; manual job re-trigger tooling in V1. → Phases 4, 5.

**Phase propagation:** Phases 2, 3, 4, 5 updated below.

**Whole-Plan Consistency Sweep**
- Re-read `plan.md` + all 6 phase files.
- Fixed stale "a day's data" → "tournament's data-to-date" in Phase 3 overview (coverage decision).
- Aligned `articles.status='published'` semantics across Phases 1 (schema), 3 (set on Editor success), 4 (serve published only), 5 (keep-last-good on failure). Consistent.
- Manual re-trigger entrypoint (`python -m app.pipeline.run`) defined in Phase 3, reused in Phase 5. Consistent.
- DeepSeek model = `deepseek-chat` consistent across plan + Phase 3.
- **Unresolved contradictions: none.**

## Implementation Log

### Session 2 — 2026-06-19 (`/cook plan.md --auto`)

**All 6 phases implemented.** 35 backend tests passing; frontend (Next.js 16 + Tailwind v4) builds clean with backend down; live integration smoke test passed (Postgres → migrations → seed → API ↔ standings).

**Verified locally**
- `docker compose up postgres` + `alembic upgrade head` → 5 tables (incl. migration 0002).
- `/health`, `/api/briefs` (`[]`), `/api/briefs/latest` (404), `/api/standings` (12 groups, deterministic qualification) all serving.
- `standings_math` best-thirds + tiebreak unit-tested; DST TZ-guard tested across AEST & AEDT.

**Code review (mandatory) — found + fixed before sign-off:**
- **B1 (BLOCKER, fixed):** deterministic `qualification_status` was computed but never reached the UI (UI used a positional heuristic) → violated the #1 non-negotiable rule. Fixed end-to-end: migration 0002 adds `standings.qualification`; `collect.py` always persists the *computed* tables + qualification; API exposes it; UI consumes it; regression test added (`test_qualification_flow.py`).
- **H1 (fixed):** token/cost logging always recorded 0 → now captured via `with_structured_output(..., include_raw=True)`.
- **H2 (fixed):** fragile JSON-mode kwarg → switched to `make_structured_client` (also removed dead code).
- **H3 (fixed):** `compute_group_table` loop-leaked `group_name` → derived once.
- **M2/M3 (fixed):** added indexes (`standings.snapshot_date`, `articles(status, brief_date)`); removed outer graph retry that double-paid DeepSeek.
- **M1 (accepted V1 trade-off, flagged):** Postgres firewall = allow-Azure-services; tighten via VNet before public launch.

**Deferred to user (external dependencies / high-risk):**
1. `API_FOOTBALL_KEY` — to run the live collector against WC 2026 data.
2. `DEEPSEEK_API_KEY` — to generate a real brief (`python -m app.pipeline.run --date YYYY-MM-DD`).
3. Azure subscription + `az` — live deploy via `infra/*.bicep` (IaC written, validated by review only; `az bicep build` recommended before first deploy).
4. Not committed to git — awaiting user approval.
