---
title: "100% Prototype UI + Real-Data Parity"
status: complete
created: 2026-06-20
source: ck_plans/reports/brainstorm-to-planner-260620-1123-prototype-ui-data-parity-report.md
mode: tdd
blockedBy: []
blocks: []
---

# 100% Prototype UI + Real-Data Parity

Bring the running Next.js app to **pixel-perfect parity** with the 6 HTML prototypes, refining existing Tailwind v4 components (no wholesale CSS port), with **every prototype visual element backed by real backend data** (no synthetic seeding). Verified via a screenshot diff loop.

All strategic decisions are locked in the brainstorm report (`source` above). This plan executes them.

## Context

- App already implements all 6 screens wired to real FastAPI data. This is a **fidelity + completeness pass**, not a rebuild.
- Three prototype elements are missing AND lack backing data: **Sparkline** and **ResultChip** (both driven by per-team recent finished matches — verified, not a snapshot trend) and **SkeletonCard** (loading states).
- Predecessor plan `260619-1030-world-cup-intelligence` (status: implemented) shipped the screens this plan refines. Not a blocking dependency.

## TDD note (honest)

- **Backend** has pytest (6 test files) → Phase 1 is true tests-first.
- **Frontend** has **no** test harness. Phase 2 adds a *minimal* vitest setup for **pure data→view helpers only** (sparkline point→path, form→chips). Presentational/pixel fidelity is verified by the **Phase 3 screenshot loop**, not DOM unit tests (KISS / YAGNI — no heavy component-DOM testing).

## Phases

| # | Phase | Status | Depends on |
|---|-------|--------|-----------|
| 1 | [Backend Data Backing](phase-01-backend-data-backing.md) | complete | — |
| 2 | [Frontend Component Parity](phase-02-frontend-component-parity.md) | complete | 1 |
| 3 | [Visual QA Parity Loop](phase-03-visual-qa-parity-loop.md) | complete | 2 |

Execution is sequential. Within each phase, follow project convention: **data → core → ui**.

## Locked decisions

- Pixel-perfect parity, all 6 screens (Home, Brief detail, Standings, Fixtures, Archive, Changelog).
- Refine Tailwind v4 components; keep design tokens; no wholesale CSS port.
- Back every visual with real data; **graceful-degrade** when tournament data is thin (render only when real data points exist; else hide/neutral placeholder).
- Verification = screenshot diff loop at desktop + mobile.

## Out of scope

- Synthetic/seeded demo history (explicitly rejected).
- New screens, backend pipeline/LLM changes, DB migrations (existing `standings` + `matches` tables suffice).

## Key dependencies

- Running backend + Postgres with collected data (docker-compose).
- Prototypes served as static HTML for visual comparison.
- `claude-in-chrome` (or equivalent) for screenshots in Phase 3.

## Validation Log

### Session 1 — 2026-06-20 (validate)

**Verification Results** (Standard tier — Fact Checker + Contract Verifier, 3 phases)
- Claims checked: 8 | Verified: 6 | Failed: 1 | Unverified: 1
- **VERIFIED:** standings table snapshot-keyed (history accrues); `matches` has scores+status+kickoff; `standings.team` and `matches.home_team/away_team` share API-Football `.name` origin (`api_football.py:94-113`) → join safe; backend pytest exists (6 files); frontend has no test harness; all named components/pages exist.
- **FAILED (corrected):** Plan claimed Sparkline = standings position/points trend over snapshots. Source (`prototypes/s03-standings.html` sparkline `aria-label="form: win win draw"`; `s01-brief-list.html:46-48` result-chips `"W BRA 3–1 SRB"`) shows **Sparkline + ResultChip are both recent-form views** of recent finished matches. Trend-over-snapshots is used by no prototype element.
- **RESOLVED (was unverified):** "finished match" definition — code only had `_NOT_STARTED` (`api_football.py:15-16`), no strict finished set.

**Decisions confirmed**
1. **Data model:** User chose to **keep the trend endpoint** in addition to the recent-results feed. Trend is built standalone with **no UI consumer** (off parity critical path). Sparkline is driven by `recent_results`, not trend.
2. **Result shape:** Full match detail — `recent_results: [{outcome, home_team, away_team, home_score, away_score, kickoff_utc}]`.
3. **Finished definition:** Strict `{FT, AET, PEN}`; in-play and not-started excluded.
4. **Window size:** Last **5** results per team (prototype shows 3; sparkline scales to up to 5 — visual QA judges line shape, not point count).

**Phase propagation:** Phase 1 rewritten (recent_results model + strict finished set + trend kept as secondary). Phase 2 updated (Sparkline/ResultChip driven by `recent_results`; `lib/form.ts`→`lib/results.ts`; no trend fetcher).

### Whole-Plan Consistency Sweep
- Re-read `plan.md` + all 3 phase files. Removed stale "standings trend"/`recent_form`/`TrendPoint`/`getStandingsTrend`/`formToChips` references; replaced with `recent_results`/`RecentResult`/`resultsToChips`. Window 5 consistent across phases. Trend endpoint consistently marked "no UI consumer." No unresolved contradictions.
- **Recommendation: proceed to implementation.**

## Implementation Log

### Session 2 — 2026-06-20 (cook --auto, tdd)

**Phase 1 — Backend Data Backing (complete).** Added `RecentResult` model + `recent_results` (default `[]`) to `StandingRow`; pure helpers `match_outcome`, `recent_results_by_team` (strict `{FT,AET,PEN}`, most-recent-first, cap 5, null-score excluded), `shape_trend`; new `GET /api/standings/trend`. TDD: `test_recent_results.py` (11) + `test_standings_trend.py` (4) written first. **Backend suite: 67 passed.** Live-verified: 48 rows backed with real results; 148 result items all scored; trend ordered + graceful on unknown team.

**Phase 2 — Frontend Component Parity (complete).** Pure helpers `lib/sparkline.ts` + `lib/results.ts` (vitest, tests-first, 13 passed); components `sparkline.tsx`, `result-chip.tsx`, `skeleton-card.tsx` (all server components); `RecentResult` + `recent_results?` in `lib/api.ts`; Sparkline wired into standings Form column; home "Recent results" chip strip from standings payload (deduped, home-perspective); 6 `loading.tsx`; additive `globals.css` (chip/sparkline/skeleton + reduced-motion). **`next build` + lint clean.**

**Phase 3 — Visual QA Parity Loop (complete).** Screenshot diff app (host dev :3001) vs prototypes (:3002). Drift fixed: standings 2-col→1-col grid so the new sparkline column fits (matches prototype full-width layout). All 6 screens signed off; home + standings also verified at 390px. No horizontal body scroll; standings table scrolls internally; reduced-motion honored. (Dev-only `cz-shortcut-listen` hydration notice = ColorZilla extension, not a code issue.)

**Code review:** clean — no blocker/high/medium; all acceptance criteria met. Applied one clarity comment (ISO-string sort assumption in `page.tsx`).

**Per-screen sign-off:** S-01 ✓ S-02 ✓ S-03 ✓ S-04 ✓ S-05 ✓ S-06 ✓
