---
phase: 1
title: Timeline & Scorer Detail (A–D)
status: completed
priority: P1
dependencies: []
---

# Phase 1: Timeline & Scorer Detail (A–D)

## Overview

Surface event detail the poll already carries: assists on goals (A), substitution on↔off (B), VAR rows (C) in the Key-moments timeline, and penalty/own-goal markers in the live banner scorers strip (D). Pure-logic additions to `lib/match.ts` are tested first; components then consume them.

## Requirements

- Functional: timeline goal rows show the assister; subst rows show both players; VAR events render a dedicated icon + label from `detail`; the banner strip marks penalties and own goals.
- Non-functional: no new API calls, no backend change. Pure helpers stay unit-tested. Never fabricate data — render only fields present on `MatchEvent` (`detail` absent ⇒ no marker).

## Architecture

`MatchEvent` (already normalized) carries `minute, extra, type, detail, player, assist, team, side`. Data is already in the 30s frontend poll / SSR payload. `buildTimeline` in `frontend/lib/match.ts` produces `TimelineRow[]`; `goalscorers` produces `ScorerEntry[]` with `goals[].detail`. Extend the row shape and the strip's rendering — no data-layer change.

### Substitution direction (the one unknown)

API-Football's `subst` event puts one player in `player` and the other in `assist`; which is on vs. off has been historically inconsistent. `normalize_events` is a passthrough (confirmed in `test_match_events.py::test_substitution_event`), so the interpretation is purely frontend. **Verify before writing copy** (see Step 1) — do not assume.

## Related Code Files

- Modify: `frontend/lib/match.ts` — add `assist` to `TimelineRow`; add a `subOnOff(event)` helper returning `{ on, off }`.
- Modify: `frontend/lib/match.test.ts` — tests for the above (written first).
- Modify: `frontend/components/match-timeline.tsx` — render assist (A), sub on↔off (B), VAR branch in `icon()`/`typeLabel()` (C).
- Modify: `frontend/components/match-scorers-strip.tsx` — penalty/OG marker (D), consistent with `goalLabel()` in `goalscorers.tsx`.
- Reference (do not change): `frontend/components/goalscorers.tsx` (`goalLabel` marker convention), `frontend/lib/api.ts` (`MatchEvent`).

## Implementation Steps

1. **Verify subst direction (spike, do first).** Query a real stored substitution event:
   `psql "$DATABASE_URL" -c "select events_json from matches where events_json::text ilike '%subst%' limit 1;"`
   Inspect which of `player`/`assist` is the incoming player. If the DB has no subst yet (early in a match day), fall back to API-Football's documented convention (`player` = in, `assist` = out) and leave a one-line comment noting the source. Record the finding in the success criteria below.
2. **(TDD) Write `lib/match.test.ts` cases first:**
   - `buildTimeline` goal row carries `assist` (currently dropped).
   - `subOnOff` returns `{ on, off }` matching the verified direction; tolerates a missing second name (one side null).
   - non-goal/non-subst rows unaffected (regression guard on existing running-score tests).
3. **Implement `lib/match.ts`:** add `assist: string | null` to `TimelineRow` and populate it in `buildTimeline`; add `subOnOff(e: MatchEvent): { on: string | null; off: string | null }`. Run vitest → green.
4. **A — timeline assist:** in `match-timeline.tsx`, append `assist <name>` to goal-row meta when `r.assist` is set (mirror `goalLabel`'s "assist X" wording).
5. **B — timeline subst:** for `subst` rows, render `on ↔ off` using `subOnOff`. Keep the existing sub icon.
6. **C — VAR:** add a `Var` branch to `icon()` (distinct mark, reuse the muted palette) and `typeLabel()` (surface `detail`, e.g. "Goal cancelled", "Penalty confirmed"); default unknown VAR detail to "VAR".
7. **D — strip markers:** in `match-scorers-strip.tsx`, switch from rendering bare `minutes` to mapping `ScorerEntry.goals` so each goal can append `(pen)` for "Penalty" / `(o.g.)` for "Own Goal" detail; open-play goals stay unmarked.
8. Run `npm run test` (vitest) and the match-page e2e; confirm green.

## Success Criteria

- [ ] Subst direction verified against real data (or documented fallback) and noted here.
- [ ] `lib/match.test.ts` covers timeline-assist and `subOnOff`; all vitest green.
- [ ] Timeline shows assister on goals, both players on subs, and a distinct VAR row with its detail.
- [ ] Banner strip marks penalties `(pen)` and own goals `(o.g.)`; open-play goals unmarked.
- [ ] No new network calls; no backend files touched.

## Risk Assessment

- **Subst direction wrong** → mitigated by Step 1 verification + a `subOnOff` unit test that is trivial to flip.
- **VAR detail strings vary** → render `detail` verbatim with a safe "VAR" default; never invent text.
- **Strip refactor regresses layout** → keep home/away alignment classes; change only inner goal mapping.
