---
phase: 3
title: "UI: components + route"
status: complete
priority: P1
dependencies: [2]
effort: "L"
---

# Phase 3: UI — components + adaptive route

## Overview

Build the `/match/[fixture_id]` route as a server component that fetches the fixture + standings, derives state via `matchState`, and composes the three layouts (S08/S07/S10) from existing + new components. Live state wraps dynamic parts in a client component polling every 30s.

## Requirements

- Functional:
  - Route `frontend/app/match/[fixture_id]/page.tsx` (server, `dynamic = "force-dynamic"`); 404 via `notFound()` on unknown id.
  - Three layouts per the brainstorm composition; forecast card present in all three, badged experimental.
  - Live layout polls `/api/fixtures/{id}` (or reuses `/api/fixtures/live` filtered) every 30s and updates score/clock/timeline without reload.
- Non-functional: reuse existing components and design tokens; no new CSS framework; accessible (`aria-label`s mirror prototypes); no fabricated data.

## Architecture

**Reuse:** `NextMatchCard` (preview hero), `LiveMatchCard` styling/poll pattern (live hero), `TeamFlag`, `StakeCard`/`StandingsTable`, `ResultChips`/`Sparkline` (form), `LocalTime`, `Countdown`.

**New components** (`frontend/components/`):
- `match-hero-final.tsx` — `.is-final` banner variant (final score + banner goalscorers).
- `match-timeline.tsx` — renders `buildTimeline(events)` as the `mt-list` (goal/card/subst icons, minute, running score).
- `goalscorers.tsx` — basic scorer cards from `goalscorers(events)` (flag, name, minute(s), goal type). **No** role/#/photo/notes.
- `form-compare.tsx` — two-team last-5 pips from standings `recent_results`.
- `qualification-stakes.tsx` — group-table slice + state-framed heading (see decision below).
- `forecast-card.tsx` — static placeholder from `placeholderForecast`, "Model preview · experimental" badge + illustrative note.
- `forecast-outcome.tsx` — finished-only slim conclusion: comparison cells (forecast pick vs actual result) + auto `forecastOutcome` hit/miss badge, under the experimental label. No prose.
- `match-live.tsx` — `"use client"` wrapper that takes the initial `FixtureDetail`, polls every 30s, and re-renders hero + timeline + goalscorers.

**Decision — qualification stakes data (KISS, honest):** v1 renders the **persisted standings group slice** for the match's group via `getStandings()`.
- Finished → snapshot already reflects the result → heading "What it means for the group · after Matchday N".
- Live/Preview → render current standings, heading "What's at stake" / "Group standings" — **labelled as current, not a fabricated projection.**
- The S07 "if the score holds" recompute (apply live score → re-sort via `standings_math`) is a real-data stretch deferred to a follow-up; do NOT invent projected points in v1. Note this limitation in the UI heading copy, not with fake numbers.

**Layout composition:**
- Preview: `NextMatchCard` → `forecast-card` → `form-compare` → `qualification-stakes`.
- Live (in `match-live`): live hero → `forecast-card` (pre-match) → `match-timeline` → `goalscorers` → `form-compare` → `qualification-stakes` (current).
- Finished: `match-hero-final` → `forecast-card` → `forecast-outcome` → `match-timeline` → `goalscorers` → `qualification-stakes` (confirmed).
- All states: provenance footer + "Read the full brief →" ghost button as in prototypes.

## Related Code Files

- Create: `frontend/app/match/[fixture_id]/page.tsx`
- Create: `frontend/components/{match-hero-final,match-timeline,goalscorers,form-compare,qualification-stakes,forecast-card,forecast-outcome,match-live}.tsx`
- Modify: `frontend/app/globals.css` only if a prototype class (e.g. `forecast-card`, `mt-list`, `scorers`, `fc-outcome`) is not already present (check first; prototypes reference `components.css` classes that may need porting).
- Reference: `frontend/components/live-match-card.tsx` (poll pattern), `frontend/components/next-match-card.tsx`, `prototypes/components.css` (class definitions to port).

## Implementation Steps

1. Audit `globals.css` for the prototype classes used by the new sections; port only the missing ones from `prototypes/components.css` (forecast-card, fc-*, mt-list/mt-*, scorers/scorer-*, fc-outcome/fc-compare). Keep tokens.
2. Build the new presentational components against Phase 2 helpers (props are already-shaped data; components do no logic).
3. Build `page.tsx`: `await params`, `getFixture(id)` → `notFound()` if null; `getStandings()`; `matchState`; branch to layout. Pass live state through `match-live`.
4. Build `match-live.tsx` client wrapper following the 30s poll pattern from `live-match-card.tsx`.
5. Manual verify (see Phase 4) — render an upcoming, a live, and a finished fixture.
6. `cd frontend && npm run build` + `npm run lint` clean.

## Success Criteria

- [ ] `/match/[fixture_id]` renders preview/live/finished layouts; unknown id → 404.
- [ ] Forecast card appears in all states, unmistakably badged experimental; it is the only placeholder.
- [ ] Finished state shows the slim forecast-vs-result conclusion with an auto hit/miss badge and no prose.
- [ ] No fabricated stats/H2H/squad content; qualification stakes uses real standings with honest framing.
- [ ] `npm run build` and `npm run lint` pass.

## Risk Assessment

- **Live poll** double-fetching / stale closure — reuse the proven `live-match-card.tsx` pattern (useRef flight guard) rather than reinventing.
- **Missing CSS classes** — prototypes link `components.css` not yet fully ported; step 1 audits and ports only what's missing to avoid duplicate/conflicting rules.
- **Thin preview page** (~4 blocks) is expected and accepted per the brainstorm; do not pad with fake sections.
