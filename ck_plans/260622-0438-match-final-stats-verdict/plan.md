---
title: Finished Match Page — Stats + Verdict (S-10 v2)
description: >-
  Close the S-10 fidelity gap: add real match statistics (incl. xG) and an
  LLM-narrated per-match verdict to the finished-match page.
status: completed
priority: P2
branch: fix/goalscorer-test-shape
tags: []
blockedBy: []
blocks: []
created: '2026-06-21T18:38:28.252Z'
createdBy: 'ck:plan'
source: skill
---

# Finished Match Page — Stats + Verdict (S-10 v2)

## Overview

Completes the two sections the **finished** match page (`/match/[fixture_id]`,
state `finished`) is still missing versus the `prototypes/s10-match-final.html`
design:

1. **Match stats** — the `.stat-bars` block (possession, shots, shots on target,
   xG, corners) from real API-Football statistics. The project runs on a **paid**
   API-Football plan, so season-2026 `fixtures/statistics` (incl. xG) is available.
2. **The verdict** — the `.analysis-note` one-line read of what happened,
   **narrated by DeepSeek from pre-computed facts only** (no invented numbers).

Both follow the existing `events_json` vertical slice exactly: collector →
matches-table JSON/text column → Python-normalized `FixtureDetail` field → React
component, with a guarded once-only on-finish backfill.

Source brainstorm: this session (develop finished match page based on current design).

## Predecessor

This is the **v2 follow-up** to the completed
`ck_plans/260621-1630-match-analysis-page` plan, which shipped the finished page
and **explicitly deferred these exact sections to out-of-scope v1**: *"Match
stat-bars (possession/shots/SoT/xG/corners) … all per-match prose (… verdict …
conclusion narrative)."* Its output is shipped, so there is **no blocking
relationship** — this plan extends it.

**Mode: `--tdd`** — matching the predecessor and repo convention: each phase
writes failing tests against pure functions first (backend `pytest`, frontend
`vitest` on `lib/`). Component JSX is not unit-tested; logic lives in pure
functions (`backend/app/api/fixtures.py` shaping, `frontend/lib/match.ts`).

## Key facts (verified against codebase)

- **`matches` table** (`backend/app/data/repository.py:15`) has columns through
  `events_json` (JSON), `stage`, `updated_at`. It does **not** have a statistics
  or verdict column → **a migration is required** (unlike the predecessor, whose
  `events_json` pre-existed). Alembic head is **`0006`** (`backend/db/migrations/versions/`).
- **Collector** `APIFootballClient` (`backend/app/data/api_football.py`):
  `_get(path, params)` helper (`:140`), `get_events` (`:224`, calls
  `/fixtures/events`). No `get_fixture_statistics` yet → **add one** calling
  `/fixtures/statistics`.
- **Backfill** (`backend/app/data/collect.py`): `backfill_finished_events`
  (`:163`) is the guarded once-only on-finish pattern; `select_fixtures_needing_events`
  lives in `app/api/fixtures.py`. The collector mutates match records in place
  (`m.events = …`, `:190`). Extend this pass to also fetch stats + trigger verdict.
- **LLM** (`backend/app/pipeline/`): `nodes_editor.py` / `nodes_analyst.py` use
  `make_structured_client(Model)` from `app/llm/deepseek.py` + `client.invoke([...])`;
  system prompts in `prompts.py` already enforce *"Do NOT invent statistics,
  standings positions, or scores."* The brief is **keep-last-good** (persist only
  on success) — mirror that for the verdict.
- **API** (`backend/app/api/fixtures.py`): `FixtureDetail(FixtureRow)` (`:85`)
  exposes only `events`; shaping is pure functions (`normalize_events`, `:128`).
- **Frontend**: `frontend/app/match/[fixture_id]/page.tsx` finished branch
  (lines 67-95) renders hero → forecast → outcome → timeline → goalscorers →
  stakes → footer. `lib/api.ts` `FixtureDetail` mirrors the backend. CSS class
  families are ported **verbatim** from `prototypes/components.css` into
  `frontend/app/globals.css` (predecessor decision); `.stat-bars`/`.sb-*` and
  `.analysis-note`/`.an-eyebrow` are **not yet** in `globals.css`.
- **Stack caveat** (`frontend/AGENTS.md`): this is a *modified* Next.js — read
  `node_modules/next/dist/docs/` before writing route/server-component code.

## Acceptance criteria

1. A finished fixture with statistics renders the **Match stats** `.stat-bars`
   block (possession, shots, SoT, xG, corners) in the S-10 order, with
   Python-computed bar percentages — no fabricated values.
2. A finished fixture renders **The verdict** `.analysis-note` block with
   DeepSeek-narrated prose grounded only in score / scorers / standings facts.
3. **Graceful degradation:** a finished fixture with no statistics shows **no**
   stats section (no empty scaffold); a fixture with no verdict (LLM failed /
   keep-last-good empty) shows **no** verdict block.
4. Verdict generation never overwrites a good stored verdict with an empty one,
   and a failed stats/verdict step never aborts the collect (logged + skipped).
5. Section order on the finished page matches S-10: hero → **verdict** →
   forecast → forecast-vs-result → timeline → goalscorers → **match stats** →
   group impact → footer. Footer provenance credits the per-match verdict model.
6. New pure functions (stats normalize/percentages, verdict fact-bundle builder)
   are covered by tests written before their implementation; full backend
   `pytest` + frontend `vitest` suites and `npm run build` + `eslint` pass.

## Out of scope

- Live (S-07) and preview (S-08) states — this plan touches the **finished**
  branch only. (Stats could later extend to live, but not here.)
- Any real prediction/forecast model — the forecast card stays the badged
  illustrative placeholder it already is.
- Penalty-shootout winner surfacing (a pre-existing predecessor follow-up).
- Backfilling stats/verdict for matches that finished before this ships beyond
  what the standard guarded on-finish pass picks up (one-shot admin reprocess is
  optional, see Phase 5 risks).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Data & collector](./phase-01-data-collector.md) | Completed |
| 2 | [Verdict pipeline](./phase-02-verdict-pipeline.md) | Completed |
| 3 | [API surface](./phase-03-api-surface.md) | Completed |
| 4 | [Frontend](./phase-04-frontend.md) | Completed |
| 5 | [Integration & validation](./phase-05-integration-validation.md) | Completed |

**Order/deps:** 1 → 2 → 3 → 4 → 5. Phase 2 (verdict) needs the columns + fact
inputs from Phase 1. Phase 3 exposes both columns. Phase 4 consumes the API.
Phase 5 validates end-to-end. (Phases 1 and 2 are both backend and could be
implemented together, but the migration + collector in 1 is the dependency root.)

## Dependencies

- Builds on completed `ck_plans/260621-1630-match-analysis-page` (shipped; no block).
- External: paid API-Football plan with season 2026 statistics access
  (`API_FOOTBALL_KEY`, `API_FOOTBALL_SEASON=2026`); `DEEPSEEK_API_KEY` for the verdict.

## Risks

- **Per-match stats availability/coverage.** Even on paid, an individual fixture
  may lack some stat types (e.g. xG for an obscure match) → normalize must omit
  missing bars, not zero-fill. Mitigated by Phase 3 shaping + Phase 1 verifying
  one real `/fixtures/statistics` response first.
- **Verdict fabrication.** The one generative surface. Mitigated by feeding the
  model a structured pre-computed fact bundle and a constrained no-invention
  prompt (mirrors `prompts.py`), plus keep-last-good and a visible provenance
  badge. Do not pass raw free-text the model could embellish.
- **Extra API calls.** One `/fixtures/statistics` call per newly-finished match
  per collect (guarded once-only, same as events) — negligible on the paid plan.

## Implementation log — 2026-06-22 (all 5 phases, TDD)

- **Phase 1:** migration `0007` (statistics_json/verdict_text/verdict_model on
  `matches`; down/up round-trip verified); `Match` fields + `upsert_matches`
  clobber-guards; `get_fixture_statistics`; `select_fixtures_needing_statistics`
  (DRY `_finished_fixtures_missing`); `backfill_finished_statistics` in `collect.run`.
- **Phase 2:** `app/pipeline/verdict.py` — pure `build_match_verdict_facts`
  (own-goal credit reversal handled) + `generate_match_verdict` (retry-twice,
  keep-last-good); `VERDICT_SYSTEM`/`VERDICT_USER` no-invention prompts;
  `backfill_finished_verdicts` (skips when no `DEEPSEEK_API_KEY`).
- **Phase 3:** `MatchStat` + pure `normalize_statistics` (Python %; omit missing;
  name-match w/ order fallback hardened per review); `FixtureDetail` +
  `get_fixture` carry `statistics`/`verdict`/`verdict_model`.
- **Phase 4:** `lib/api.ts` types; `components/match-stats.tsx`; verdict
  `.analysis-note` + stats in S-10 order on the finished branch; footer credits
  verdict model; CSS ported into `globals.css`.
- **Phase 5:** `seed_finished_match.py`; end-to-end verified via `get_fixture` on
  a seeded row (5 stat bars, %s sum to 100; verdict + model present); graceful
  degradation verified (clear → 0 stats / null verdict).

**Gates:** backend pytest **141 passed** (+27 new); frontend vitest **34**;
`npm run build` + TS clean; eslint clean on changed files (5 pre-existing errors
in untouched files). **code-reviewer: no blocking issues** (all 5 acceptance
criteria + 4 regression touchpoints verified); one Low hardening fix applied.

**Outstanding manual gate (needs API spend):** run one real `collect` against a
finished season-2026 fixture to confirm the live `/fixtures/statistics` payload
maps as expected; adjust the `_STAT_LABELS` map if reality differs.

**Commit note:** the working tree also carries pre-existing, unrelated changes
(`prototypes/components.css`, `prototypes/s11-betting-recommendation.html`, and
S-11 lines in `prototypes/README.md`) from before this work — stage selectively.
