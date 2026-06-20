---
phase: 2
title: "Frontend Component Parity"
status: complete
priority: P1
effort: "1.5d"
dependencies: [1]
---

# Phase 2: Frontend Component Parity

## Overview
Add the three missing prototype components (Sparkline, ResultChip, SkeletonCard), wire per-route Suspense loading, consume Phase 1 data, and refine every existing component to match the prototype CSS — keeping Tailwind v4 + tokens. Per validation: Sparkline + ResultChip are **both driven by `recent_results`** (per-team recent finished matches), NOT a trend feed.

## Requirements
- **Functional:**
  - `<Sparkline>` renders a line from a team's `recent_results` outcome sequence (W=2, D=1, L=0), up to 5 points; graceful-degrade (nothing/neutral when < 2 points); respects `prefers-reduced-motion` (no line-draw animation). Prototype draws 3 points — ours scales to up to 5 (user decision); Phase 3 judges line shape, not point count.
  - `<ResultChip>` renders each `recent_results` item as `W BRA 3–1 SRB` (outcome letter + scoreline); nothing when `[]`.
  - `<SkeletonCard>` + per-route `loading.tsx` Suspense boundaries.
  - `lib/api.ts`: add `RecentResult` type + `recent_results` on `StandingRow`. Trend endpoint exists in backend but has **no UI consumer** — no fetcher wired (avoids dead code).
  - Refine: changelog timeline (`.cl-*`), brief prose, standings table, fixtures, archive, hero/compact cards, stars strip — to match prototype look.
- **Non-functional:** no wholesale CSS port; reuse `globals.css` tokens; no new heavy deps beyond a minimal vitest dev-setup.

## Architecture
- **Data→view logic extracted as pure functions** (testable without DOM):
  - `sparklinePath(points: number[], w, h): string` — normalize outcome values (W=2/D=1/L=0) → SVG polyline/path `d`.
  - `resultsToChips(results: RecentResult[]): {key, label, variant, score}[]` — map each finished match → chip props (`W BRA 3–1 SRB`).
- Components are thin wrappers around these helpers. Sparkline = inline SVG (matches prototype's self-contained, no-dep approach; mirror `.sparkline` styling).
- **Loading states:** server components stream behind `loading.tsx`; skeleton markup mirrors prototype `.skeleton-card`/`.skeleton-line`.
- Reduced-motion via CSS media query in `globals.css` (consistent with prototype gating).

## Related Code Files
- Create: `frontend/components/sparkline.tsx`, `frontend/components/result-chip.tsx`, `frontend/components/skeleton-card.tsx`
- Create: `frontend/lib/sparkline.ts` (pure helper), `frontend/lib/results.ts` (pure helper)
- Create: `frontend/app/loading.tsx`, `frontend/app/standings/loading.tsx`, `frontend/app/fixtures/loading.tsx`, `frontend/app/archive/loading.tsx`, `frontend/app/changelog/loading.tsx`, `frontend/app/brief/[date]/loading.tsx`
- Create (test setup): `frontend/vitest.config.ts`, `frontend/lib/sparkline.test.ts`, `frontend/lib/results.test.ts`
- Modify: `frontend/lib/api.ts`, `frontend/components/standings-table.tsx`, `frontend/components/brief-card.tsx`, `frontend/app/changelog/page.tsx`, `frontend/app/globals.css`, and other components needing fidelity tweaks (driven by Phase 3 diffs)
- Modify: `frontend/package.json` (add `vitest` + `test` script only)
- Reference: `prototypes/components.css`, `prototypes/styles.css`, `prototypes/interactions.js` (sparkline/animation behavior)

## Implementation Steps
1. Add minimal vitest setup (`vitest`, config, `test` script). No RTL/jsdom unless a helper needs DOM.
2. **(TEST FIRST)** `sparkline.test.ts`: 0/1 point → empty; flat series; normalization bounds; monotonic mapping; up to 5 points. Then implement `sparklinePath`.
3. **(TEST FIRST)** `results.test.ts`: outcome→variant mapping, scoreline label, empty → `[]`. Then implement `resultsToChips`.
4. Build `<Sparkline>`, `<ResultChip>`, `<SkeletonCard>` over the helpers; match prototype class styling via tokens.
5. Extend `lib/api.ts` (`RecentResult` type + `recent_results` on `StandingRow`); wire Sparkline + ResultChip into standings rows (S-03) and home result strip (S-01) from `recent_results` already in the standings payload.
6. Add `loading.tsx` Suspense boundaries for all 6 routes.
7. Refine remaining components/screens to prototype look (changelog timeline, prose, cards, fixtures, archive). Detailed drift list comes from Phase 3.

## Success Criteria
- [ ] `sparkline.test.ts` + `results.test.ts` written first, passing; `npm run test` green.
- [ ] Sparkline + ResultChip render from real API data; invisible when data thin (no fabricated visuals).
- [ ] Skeletons appear via `loading.tsx` on navigation to each route.
- [ ] `next build` passes (Next 16 / React 19); no console errors; reduced-motion honored.

## Risk Assessment
- **Server components have no client loading spinner** — skeleton parity depends on `loading.tsx` Suspense, not a CSS class. Already designed in.
- **Tailwind v4 token drift** — exact prototype spacing/shadows may need raw values; keep them in `globals.css`, not scattered inline. Mitigation: Phase 3 catches residual drift.
- **Next 16 breaking changes** — per `frontend/AGENTS.md`, consult `node_modules/next/dist/docs/` before adding `loading.tsx`/Suspense patterns.
