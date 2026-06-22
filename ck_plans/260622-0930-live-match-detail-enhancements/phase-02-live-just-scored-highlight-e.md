---
phase: 2
title: "Live Just-Scored Highlight (E)"
status: pending
priority: P2
dependencies: []
---

# Phase 2: Live Just-Scored Highlight (E)

## Overview

When a new event (goal, card, sub, VAR) arrives on a live poll, briefly emphasize it so a live watcher notices what just happened. Pure frontend, derived by diffing the event list across polls. No backend change.

## Requirements

- Functional: events present in the latest poll but absent from the previous one get a transient highlight (CSS animation) that auto-clears. Goals get the strongest emphasis.
- Non-functional: nothing flashes on the initial SSR render (the first payload is "already seen"). Honor `prefers-reduced-motion`. No new network calls.

## Architecture

`MatchEvent` has no stable ID, so identity is a composite key: `minute|extra|type|player|side`. `match-live.tsx` already polls `/api/fixtures/{id}` every 30s into `fixture` state. Add a `useRef<Set<string>>` of seen keys, seeded from the initial payload so first paint highlights nothing. On each `setFixture`, compute keys present now but not in the ref, mark them as "fresh" for the current render, then fold them into the seen set. Pass freshness down to `MatchTimeline` (and optionally the scorers strip) which applies a highlight class.

The diff is pure → tested in `lib/match.ts`; the ref/lifecycle wiring lives in the client component.

## Related Code Files

- Modify: `frontend/lib/match.ts` — add `eventKey(e: MatchEvent): string` and `freshEventKeys(prevKeys: Set<string>, events: MatchEvent[]): string[]`.
- Modify: `frontend/lib/match.test.ts` — tests for both (written first).
- Modify: `frontend/components/match-live.tsx` — seen-keys ref seeded from `initial`, compute fresh keys on poll, pass to timeline.
- Modify: `frontend/components/match-timeline.tsx` — accept an optional `freshKeys: Set<string>` (or per-row boolean) and apply a highlight class.
- Modify: `frontend/app/globals.css` (or the existing match stylesheet) — `@keyframes` flash + `.mt-item.is-fresh`, gated by `@media (prefers-reduced-motion: reduce)`.

## Implementation Steps

1. **(TDD) Write `lib/match.test.ts` cases first:**
   - `eventKey` is stable for identical events and distinct across minute/type/player/side.
   - `freshEventKeys(prev, events)` returns only keys not in `prev` (e.g. prev seeded with two goals + one new goal arrives → returns the one new key).
   - empty/None events → `[]`.
2. **Implement `lib/match.ts`:** `eventKey` joins `minute, extra ?? "", type, player ?? "", side ?? ""`; `freshEventKeys` maps + filters. Run vitest → green.
3. **Wire `match-live.tsx`:** create `seenKeys = useRef(new Set(initial.events.map(eventKey)))`. In the poll handler, after fetching `next`, compute `fresh = freshEventKeys(seenKeys.current, next.events)`, store in component state for this render, and add all current keys to `seenKeys.current`. (Seeding from `initial` is what suppresses first-paint flashing.)
4. **Pass freshness to `MatchTimeline`:** add an optional `freshKeys?: Set<string>` prop; a row is fresh when `freshKeys?.has(eventKey(rowEvent))`. Apply `is-fresh` (and a stronger variant for goals).
5. **CSS:** add a short flash/glow keyframe; under `prefers-reduced-motion: reduce`, drop the animation (optionally keep a static accent border so the event is still distinguishable).
6. Run vitest + match-page e2e; manually sanity-check that reloading a live match does not flash existing events.

## Success Criteria

- [ ] `eventKey` / `freshEventKeys` covered by vitest; all green.
- [ ] A new event on a poll is highlighted; the same event on the next poll is not.
- [ ] Initial SSR render highlights nothing.
- [ ] Animation suppressed under `prefers-reduced-motion`.
- [ ] No new network calls.

## Risk Assessment

- **Key collisions** (two same-minute events, same player/side/type) → acceptable; worst case one highlight is skipped, never a wrong-data render. Composite key minimizes it.
- **Late-corrected events** (API revises a minute) → treated as a new key → re-highlights once. Acceptable.
- **State churn** → fresh set is per-poll render only; seen-set is a ref (no re-render). Keep the flash duration short (~2–3s) so it clears before the next poll.
