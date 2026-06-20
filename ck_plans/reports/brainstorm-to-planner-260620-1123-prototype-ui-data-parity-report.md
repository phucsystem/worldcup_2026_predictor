# Brainstorm: 100% Prototype UI + Real-Data Parity

**Date:** 2026-06-20 11:23 GMT+10 · **Branch:** main · **Status:** agreed, ready to plan

## Problem statement

React app already implements all 6 screens wired to real FastAPI data. Goal is **pixel-perfect visual parity** with the HTML prototypes, **and** every prototype visual element backed by **real** backend data (no static/illustrative values).

## Locked decisions

| Decision | Choice |
|---|---|
| Fidelity target | Pixel-perfect parity (all 6 screens) |
| CSS strategy | Refine existing Tailwind v4 components (keep tokens, no wholesale CSS port) |
| Data scope | Back every visual with real data |
| Verification | Screenshot diff loop (app vs prototype, desktop + mobile) |
| Thin-data behavior | Graceful degrade — render element only when real data points exist; else hide/neutral placeholder |
| Screen scope | All 6: Home, Brief detail, Standings, Fixtures, Archive, Changelog |

## The gap (prototype → React)

| Element | Status | Work |
|---|---|---|
| Sparkline | missing, no data | new `GET /api/standings/trend` (last N snapshots/team) + `<Sparkline>` |
| ResultChip (recent form) | missing, no data | derive W/D/L from finished `matches`; expose via API + `<ResultChip>` |
| SkeletonCard | missing | per-route `loading.tsx` Suspense boundaries + skeleton component |
| Changelog timeline | basic | refine to match `.cl-*` prototype styling |
| Flags, countdown, stars, position-delta, knockout bracket, cards, prose | exist | visual-diff refinement to match prototype exactly |

## Key constraints (verified)

- **Standings history feasible:** `standings` table keyed by `snapshot_date`; daily collector replaces-per-date, so snapshots accrue across days → sparkline data derivable. No trend endpoint exists yet.
- **Recent form feasible:** `matches` has scores + status → W/D/L per team derivable from finished matches.
- ⚠️ **Data thin now:** early tournament (2026-06-20) → few snapshots/finished matches. Sparklines/form will be sparse until more rounds play. Handled via graceful-degrade decision.
- ⚠️ **Skeletons need architecture:** app uses server components (`force-dynamic` + server fetch). Prototype skeletons require `loading.tsx` Suspense boundaries, not just a CSS class.

## Proposed phasing (data → core → ui per project convention)

1. **Phase A — Data backing (backend):** trend endpoint + recent-form derivation + graceful-empty contracts. Touchpoints: `backend/app/api/standings.py`, `backend/app/api/fixtures.py` (or new), `backend/app/data/repository.py`, new migration if a derived field is persisted.
2. **Phase B — Component parity (frontend):** add `<Sparkline>`, `<ResultChip>`, `<SkeletonCard>` + `loading.tsx`; refine existing components screen-by-screen against prototype CSS. Touchpoints: `frontend/components/*`, `frontend/app/**/page.tsx`, `frontend/app/globals.css`, `frontend/lib/api.ts`.
3. **Phase C — Visual QA loop:** screenshot running app vs prototype HTML at desktop + mobile widths; diff; fix drift; repeat until parity. Per-screen sign-off.

## Acceptance criteria

- Each of 6 screens visually matches its prototype at desktop + mobile (screenshot diff).
- Sparkline + ResultChip render from real API data; absent/thin data degrades gracefully (no fabricated values).
- Loading states (skeletons) appear via Suspense boundaries.
- No regression in existing real-data wiring.

## Out of scope

- No synthetic/seeded demo history (explicitly rejected).
- No wholesale CSS port; no new screens; no backend pipeline/LLM changes.

## Risks

- Pixel-parity vs Tailwind-refine is iterative — visual QA loop may surface many small diffs (slowest phase).
- Thin tournament data means sparklines look empty now — expected, not a bug.
- Sparkline as inline SVG/CSS must respect `prefers-reduced-motion` (prototype gates line-draw animation).

## Unresolved questions

- None blocking. Trend window size (last 3 vs 5 snapshots) and recent-form length (last 3 vs 5) to be fixed during planning.
