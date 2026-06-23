---
phase: 3
title: "UI (component + wiring)"
status: done
effort: ""
---

# Phase 3: UI (component + wiring)

## Overview

Surface the backend `home_status`/`away_status` on the match page: add the TS types, build a
`TeamStatus` component, and slot it into the **preview** (non-live/non-finished) and **live**
branches of `/match/[fixture_id]` next to `QualificationStakes`. Update the changelog.

> Note: `matchState` (lib/match.ts) returns `"preview" | "live" | "finished"`. The
> non-live/non-finished branch is the `else` branch in `page.tsx` — referred to here as the
> "preview branch", which is what the brainstorm called "upcoming".

## Requirements

- Functional: render per-team objective line + suspended/at-risk player lists for preview
  and live fixtures; render nothing on finished or when status is absent.
- Non-functional: server-component friendly (no new client island needed — live section
  shows a static snapshot per the brainstorm); reuse existing card/badge styles; no
  horizontal scroll on mobile.

## Architecture

- **Types** in `frontend/lib/api.ts` — mirror the backend models:
  ```ts
  export interface PlayerStatus {
    player: string;
    reason: string;            // "red-card" | "yellow-accumulation" | "one-yellow"
    status: "suspended" | "at_risk";
    key_player: boolean;
  }
  export interface TeamStatus {
    objective: string;
    objective_css: string;     // "qualified" | "out" | "contention"
    unavailable: PlayerStatus[];
    at_risk: PlayerStatus[];
  }
  // extend FixtureDetail:
  //   home_status: TeamStatus | null;
  //   away_status: TeamStatus | null;
  ```
- **Component** `frontend/components/team-status.tsx` (server component):
  - Props: `home`/`away` `{ team, logo, status: TeamStatus | null }`.
  - Two columns (home/away), each: objective line (styled by `objective_css`, reusing the
    qualified/out/contention vocab already used by stake cards), then a compact list —
    "Suspended" group and "One booking away" group, key players emphasised (e.g. bold + a
    small star/marker consistent with `star-card`/badge styling).
  - Renders `null` if both sides have no status.
- **Match page wiring** `frontend/app/match/[fixture_id]/page.tsx`:
  - Build `const teamStatus = <TeamStatus home={{...fixture.home_status}} away={{...}} />`.
  - Insert in the **preview** (else) branch (after `formCompare`, before/with `stakes`) and
    pass into the **live** branch (`MatchLive` already takes `forecastSlot`/`formSlot`/
    `stakesSlot` — add a `teamStatusSlot` or place alongside). Do **not** add it to the
    finished branch.

## Related Code Files

- Create: `frontend/components/team-status.tsx`
- Modify: `frontend/lib/api.ts` (add `PlayerStatus`, `TeamStatus`, extend `FixtureDetail`)
- Modify: `frontend/app/match/[fixture_id]/page.tsx` (render in upcoming + live)
- Modify: `frontend/components/match-live.tsx` (accept + render the team-status slot, if the
  live branch routes through it)
- Modify: `frontend/public/CHANGELOG.md` (new entry, newest first — CI gate)
- Reference: `frontend/components/qualification-stakes.tsx`, `stakes/*`, `stars/star-card.tsx`
  for styling vocabulary.

## Implementation Steps

1. Add the TS interfaces to `api.ts` and extend `FixtureDetail`.
2. Build `team-status.tsx` reusing existing badge/card tokens; handle empty/null gracefully.
3. Wire into the match page preview (else) branch; thread a slot into `MatchLive` for the
   live branch (static snapshot — no polling).
4. Confirm the finished branch is untouched.
5. Add a user-facing `CHANGELOG.md` entry (newest version first).
6. Run `npm test` and `next build`; visually verify upcoming + live render and finished does
   not.

## Success Criteria

- [ ] TS types compile (strict mode); `FixtureDetail` carries the two new fields.
- [ ] Team status renders on preview + live fixtures, omitted on finished and when both
      statuses are null.
- [ ] Key players visually emphasised; suspended vs at-risk visually distinct.
- [ ] `CHANGELOG.md` updated; `npm test` + `next build` pass; no mobile horizontal scroll.

## Risk Assessment

- **Live branch wiring:** the live view routes through `MatchLive`; confirm whether to pass a
  new slot vs render adjacent. Low risk — mirror how `stakesSlot`/`formSlot` are already
  threaded.
- **Style drift:** reuse the existing stake/badge token vocabulary rather than inventing new
  colors so the section reads as native to the page.
