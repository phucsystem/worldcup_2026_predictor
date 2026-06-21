---
phase: 2
title: "Core: frontend logic"
status: complete
priority: P1
dependencies: [1]
effort: "M"
---

# Phase 2: Core — frontend pure logic (vitest)

## Overview

All non-trivial logic for the page lives in tested pure functions under `frontend/lib/`, matching the repo convention (`lib/*.test.ts`). Components in Phase 3 stay thin. No JSX is tested here.

## Requirements

- Functional pure helpers:
  - `matchState(status)` → `"preview" | "live" | "finished"` using the same status sets as the backend (`LIVE_STATUSES`, finished `FT/AET/PEN`, else preview).
  - `buildTimeline(events)` → ordered list of timeline rows with a **running score** computed from goal events (incl. own-goal handling: own goal credits the opposing side), card/subst rows carry no score. Mirrors the `mt-list` rows in S07/S10.
  - `goalscorers(events)` → grouped goal entries per side: `{ side, player, minutes:int[] }` (the basic card data — name, side, minute(s), goal type only; no role/#/notes).
  - `forecastOutcome(forecast, homeScore, awayScore)` → `{ hit:boolean, predictedSide, actualSide }` for the finished-state slim conclusion. `predictedSide` = forecast's most-likely; `actualSide` = winner or `"draw"`; `hit` = they match. Returns null if scores absent.
- Non-functional: pure, no fetch, no DOM; exported types added to `lib/api.ts` (`MatchEvent`, `FixtureDetail`) to mirror the backend models.

## Architecture

- Extend `lib/api.ts`: add `MatchEvent`, `FixtureDetail` interfaces and `getFixture(fixtureId: number): Promise<FixtureDetail | null>` using the existing `apiFetch` wrapper.
- New `lib/match.ts`: `matchState`, `buildTimeline`, `goalscorers`, `forecastOutcome`, plus the **static forecast placeholder** constant/factory `placeholderForecast(home, away)` returning the illustrative percentages + factor list shown in the prototypes (clearly a fixed placeholder, never derived from data). Keep the experimental copy strings here so the component is dumb.
- Forecast type: `Forecast { homePct, drawPct, awayPct, factors: {name, lean:"home"|"away"|"even", why}[], note }`.

## Related Code Files

- Modify: `frontend/lib/api.ts` (types + `getFixture`)
- Create: `frontend/lib/match.ts`
- Create: `frontend/lib/match.test.ts`
- Reference: `frontend/lib/live.ts` + `frontend/lib/live.test.ts` (existing pure-fn + test pattern), `frontend/lib/results.ts`

## Implementation Steps (TDD)

1. **Tests first** — `lib/match.test.ts`:
   - `matchState`: `NS`→preview; `1H/HT/2H/ET/BT/P/LIVE`→live; `FT/AET/PEN`→finished; unknown→preview.
   - `buildTimeline`: running score across multiple goals; own-goal credits opponent; non-goal events keep prior score / no score field; ordering by minute then extra.
   - `goalscorers`: groups a player's two goals into one entry with `minutes:[51,78]`; splits by side; ignores non-goal events.
   - `forecastOutcome`: home favourite + home win → hit; home favourite + draw → miss; absent scores → null.
2. Run → red.
3. Implement `lib/match.ts` + `lib/api.ts` additions.
4. `cd frontend && npm test` → green.

## Success Criteria

- [ ] `lib/match.test.ts` written first and passing; covers timeline running-score, own-goal, scorer grouping, state derivation, and forecast hit/miss.
- [ ] `getFixture` + `MatchEvent`/`FixtureDetail` types added to `lib/api.ts`.
- [ ] `placeholderForecast` is the single source of the illustrative forecast content.
- [ ] `npm test` (vitest) green.

## Risk Assessment

- **Status-set drift** between backend and frontend. Mitigation: comment in `lib/match.ts` pointing to `LIVE_STATUSES` in `fixtures.py`; same literals in both. (Single tournament feed — acceptable duplication over a shared codegen.)
- **Own-goal / VAR edge cases** in timeline scoring. Mitigation: explicit tests; unknown event types pass through without affecting score.
