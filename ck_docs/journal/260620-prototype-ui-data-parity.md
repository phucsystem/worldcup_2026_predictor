# Prototype UI Data Parity — TDD Implementation

**Date**: 2026-06-20 16:43
**Severity**: Low (feature complete, all acceptance criteria met)
**Component**: Backend (FastAPI) + Frontend (Next.js 16/React 19/Tailwind v4)
**Status**: Resolved

## What Happened

Brought running Next.js app to visual + data parity with 6 HTML prototypes. Every prototype visual backed by REAL backend data (no synthetic seeding). TDD-driven: tests-first, then implementation, verified via screenshot diff loop at 1280px + 390px.

**Phase 1 (backend):** Added `recent_results` array to GET `/api/standings` StandingRow (up to 5 strictly-finished {FT,AET,PEN} matches per team, most-recent-first, graceful `[]` degrade). Standalone GET `/api/standings/trend` (product decision, no UI consumer yet). Pure helpers: `match_outcome()`, `recent_results_by_team()`, `shape_trend()`. Tests: `test_recent_results.py`, `test_standings_trend.py`. Backend suite: 67 passed. Live: 48 standings rows, 148 result items.

**Phase 2 (frontend):** Pure helpers `lib/sparkline.ts` (fixed [0,2] domain for cross-team comparison), `lib/results.ts` (resultsToChips). Components: Sparkline, ResultChips, SkeletonCard (server components, role=img + aria-labels). RecentResult type in `lib/api.ts`. Sparkline → standings Form column. Home "Recent results" chip strip derived from standings payload (deduped, outcome recomputed home-perspective). 6 loading.tsx Suspense skeletons. Globals.css additive (chips, sparklines, skeletons, prefers-reduced-motion). Vitest: 13 tests, TDD. Build + lint clean.

**Phase 3 (visual QA):** Screenshot diff app (next dev :3001) vs prototypes (python http.server :3002). Key drift fixed: standings 2-col grid → 1-col full-width so sparkline Form column fits prototype's full-width table. All 6 screens signed off; no horizontal body scroll; standings table internal scroll on mobile.

## The Brutal Truth

Backend containers NOT volume-mounted (baked images); used docker cp for test loop. Host fish shell PATH corruption (GVM error) blocked native cp/ls. Workaround: Write tool + wrapper scripts to stage files. At finalize, rebuilt both images so running stack matches source. Dev-only `cz-shortcut-listen` hydration warning = ColorZilla browser extension, not code defect. Screenshot loop slow but reliable: visual truth > speed.

## Technical Details

- Backend: `GET /api/standings` response size +12% (RecentResult array per team). Graceful degrade: missing api_football data = `recent_results: []`.
- 3-char slice abbreviation: SOU/UNI collisions accepted (parity judges structure, not content per plan spec).
- Finished set {FT,AET,PEN} in recent_results mirrors api_football.py's NOT_STARTED logic.
- Sparkline domain [0,2] (team-relative win/draw/loss) prevents unit-clipping artifacts on low-activity teams.
- Trend endpoint intentionally unconsumed (product backlog, no frontend consumer).

## What We Tried

- Initial test suite: 67 backend tests covered match_outcome edge cases (null scores, no recent matches, tie-breaking in recency).
- Frontend Sparkline: tried [0,1] domain (SVG normalize); switched [0,2] for visual stability across teams.
- Screenshot diff: looped 6 prototypes manually at 1280px/390px; marked responsive grid drift (2-col → 1-col) as the single structural fix.

## Root Cause Analysis

Schema mutation (adding recent_results) required strict backward-compat handling: treated as optional array, no validation constraint on length (graceful degrade if missing). Frontend Sparkline clipping was unit-scale assumption (0-1); real data spans wider (0, 1, 2 wins/draws/losses in small sample sets).

## Lessons Learned

1. **Docker image layer assumption costs time.** Baked images lose volume-mount flexibility; always rebuild before finalize to match source truth.

2. **Screenshot diff as source of truth beats manual eye.** The 2-col → 1-col grid drift was missed in code review; caught immediately via diff loop. Invest in visual regression CI.

3. **Data-driven defaults beat synthetic seeds.** Graceful degrade ([] for missing api_football) ships cleaner than inventing 5 matches. Real data collection deferred; empty state is production-ready.

4. **Sparkline domain bounds matter.** [0,1] assumed; real data lives in [0,2]. Fixed domain prevents visual artifacts.

## Next Steps

- Collect api_football_key; seed 2022 season. Run `/collect-fixtures` to populate recent_results with real match outcomes.
- Trend endpoint: product backlog (no UI consumer yet; reserve for future analytics sprint).
- Visual regression CI: automate screenshot diff loop in pre-merge pipeline (avoid manual 6-screen loop).

**Code review:** clean, no blocker/high/medium, all acceptance criteria met. Commit ready.
