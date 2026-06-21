---
title: "Match Analysis Page (S07/S08/S10)"
description: ""
status: complete
priority: P2
branch: "main"
tags: []
blockedBy: []
blocks: []
created: "2026-06-21T06:48:45.540Z"
createdBy: "ck:plan"
source: skill
---

# Match Analysis Page (S07/S08/S10)

## Overview

One adaptive route `/match/[fixture_id]` rendering three states from real fixture data: **Preview** (S08, upcoming), **Live** (S07, in-play), **Finished** (S10, full-time). State is chosen by API-Football `status`. Scope is **data-backed only** — every section is real data except the win-probability forecast, which is ported as a clearly-badged static placeholder (no prediction model exists). Unbacked prototype sections (match stat-bars, team-comparison, head-to-head, players-to-watch, strengths/weaknesses, per-match prose) are explicitly out of v1.

Source brainstorm: `ck_plans/reports/260621-match-analysis-page-brainstorm.md`.

**Mode:** `--tdd` — each phase writes failing tests against pure functions first (backend pytest, frontend vitest on `lib/`), matching the repo's existing test conventions (`backend/tests/test_fixtures_shaping.py`, `frontend/lib/*.test.ts`). Component JSX is not unit-tested in this repo; logic lives in testable pure functions.

## Key facts (verified against codebase)

- `matches.events_json` column **already exists** (`sa.JSON` in `repository.py:28`) — **no migration needed**, only population.
- `APIFootballClient.get_events(fixture_id)` exists (`api_football.py:224`) but is unused.
- Live refresh path: `collect_live()` (`collect.py:128`) + `pipeline/live_poller.py`; daily path: `collect.run()` (`collect.py:39`).
- Fixtures API shaping is split into pure functions for unit tests (`api/fixtures.py`); `FixtureRow` Pydantic model lives there.
- `standings_math.py` computes deterministic group tables — reusable for the live "if score holds" projection.
- Frontend: server components fetch via `lib/api.ts` `apiFetch<T>` (`cache: "no-store"`); live polling is component-side every 30s (`live-match-card.tsx`).

## Acceptance criteria

1. `/match/[fixture_id]` renders the correct layout for an upcoming, a live, and a finished fixture; returns 404 on unknown id.
2. Live page updates score/clock/timeline on a 30s poll without full reload.
3. Every section shows only real data; the forecast card is the **sole** placeholder, unmistakably badged experimental/illustrative.
4. No fabricated stats / head-to-head / squad content anywhere.
5. Match cards on existing pages (home up-next/live, brief, fixtures, standings) link to the page.
6. New pure functions are covered by tests written before their implementation; full backend + frontend suites pass.

## Out of scope (v1)

Match stat-bars (possession/shots/SoT/xG/corners), team-comparison averages, head-to-head, players-to-watch, strengths & weaknesses, all per-match prose (live read / verdict / what-to-watch / conclusion narrative), and any real prediction engine.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Data: events + fixture endpoint](./phase-01-data-events-fixture-endpoint.md) | Complete |
| 2 | [Core: frontend logic](./phase-02-core-frontend-logic.md) | Complete |
| 3 | [UI: components + route](./phase-03-ui-components-route.md) | Complete |
| 4 | [Integration: link wiring + validation](./phase-04-integration-link-wiring-validation.md) | Complete |

## Dependencies

Builds on two **completed** plans (their output is shipped, no blocking relationship):
- `260620-1123-prototype-ui-data-parity` — established reusable components + data parity.
- `260621-0327-home-inprogress-live` — established `LiveMatchCard` + `/api/fixtures/live` polling pattern reused here.

Within this plan: Phase 2 depends on Phase 1 (`FixtureDetail` shape + events); Phase 3 depends on Phase 2 (lib helpers); Phase 4 depends on Phase 3 (route must exist to link to).

## Validation Log

### Session 1 — 2026-06-21

**Verification Results (Standard tier — Fact Checker + Contract Verifier)**
- Claims checked: 12 | Verified: 12 | Failed: 0 | Unverified: 0
- Verified: all Phase 4 components exist; Next 16 `params: Promise<>` + `await params` + `notFound()` pattern (`brief/[date]/page.tsx`); `seed_live_match.py` present; `recent_results` on `StandingRow` in `lib/api.ts`; `next-match`/`stake-card` classes already in `globals.css`; `events_json` column present (`repository.py:28`); `get_events` present (`api_football.py:224`); `collect_live`/`collect.run` present.
- Finding (confirms planned task): `forecast-card`, `fc-*`, `mt-list`, `scorers`, `fc-outcome`, `is-final`, form-pip classes are **absent** from `globals.css` (0 hits) — they exist only in `prototypes/components.css`. Phase 3 CSS-porting is real, multi-family work.

**Decisions confirmed**
1. **Live standings (Phase 3):** show the real **current** standings slice for the group, labelled as current — NOT a fabricated "if score holds" projection. The S07 projected-table recompute is a deferred follow-up; no projected numbers in v1.
2. **CSS porting (Phase 3):** port the needed class families from `prototypes/components.css` into `globals.css` verbatim (matches how `next-match`/`stake-card` already live there). Not rebuilt as Tailwind utilities.
3. **Events backfill (Phase 1):** live poller populates events for in-play matches (incl. final events at FT); daily `collect.run` backfills only finished matches still missing events, once (guarded). Not live-poller-only.
4. **Card linking (Phase 4):** add an explicit **"Match analysis →"** affordance to each card rather than wrapping the whole card in an anchor — avoids nested `<a>` with the hero's inner "Watch live on SBS" link.

**Propagation:** Phase 4 architecture + steps updated to lock the explicit affordance (nested-anchor note). Decisions 1–3 already matched the phase text as written (no edits needed).

### Whole-Plan Consistency Sweep
Re-read `plan.md` + all four phase files. Checked for stale terms, renamed APIs/fields, superseded decisions, duplicate contracts.
- Live standings: plan.md + Phase 3 agree (current table, projection deferred). ✓
- CSS porting: plan.md + Phase 3 agree (port into `globals.css`). ✓
- Events backfill: plan.md + Phase 1 agree (live poller + guarded daily backfill). ✓
- Card linking: plan.md + Phase 4 agree (explicit affordance, no whole-card anchor). ✓
- **Result: 0 unresolved contradictions.** Plan eligible for implementation.

### Session 2 — 2026-06-21 — Implementation complete

All four phases implemented in TDD order. Tests written first per phase.

- **Tests:** backend `pytest` 114 pass (was 97; +17: `test_match_events.py`, `test_fixture_detail_endpoint.py`); frontend `vitest` 34 pass (+13 `lib/match.test.ts`). `npm run build` + `eslint` clean.
- **Live validation** (seeded dev data, all 3 states + 404): upcoming/live/finished pages render correct layouts; events normalize with correct home/away sides; live-poll proxy `/api/fixtures/{id}` returns 200 w/ events; unknown id → backend 404 (page shows not-found UI at HTTP 200, matching the existing `brief/[date]` `notFound()`+`force-dynamic` behavior).
- **Code review:** DONE_WITH_CONCERNS, no Critical/High. Fixed: forecast-outcome now carries an explicit "illustrative only" note; `FormCompare` hides the "Last N" label when no results; `NextMatchCard` gains a `linked` prop so the preview hero doesn't self-link on the match page.
- **Known limitation / follow-up (not in v1 scope):** penalty-shootout knockout matches render the regulation score and classify as a draw (no winner surfaced), because `home_score`/`away_score` come from API-Football `goals.*` (regulation+ET only). Surfacing the shootout winner needs `score.penalty` plumbing in the collector + `MatchEvent`/hero changes. Group stage is unaffected; relevant only once knockouts begin.
