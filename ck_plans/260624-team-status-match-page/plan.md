---
title: "Team Status on Match Page (objective + availability)"
description: ""
status: done
priority: P2
branch: "feat/forecast-accuracy-rate"
tags: []
blockedBy: []
blocks: []
created: "2026-06-23T22:44:32.392Z"
createdBy: "ck:plan"
source: skill
---

# Team Status on Match Page (objective + availability)

## Overview

Add a **Team status** section to `/match/[fixture_id]` for **upcoming + live** fixtures only.
Per team, show two fact-based blocks:

1. **Match objective** — one deterministic line on what the team needs from this game
   (must-win / draw-enough / already-through / eliminated), extending the existing
   `qualification_status` + `group_scenarios` logic in `standings_math.py`.
2. **Availability** — players suspended (red card last game, or 2nd yellow accumulation) or
   one booking from a ban, derived *statefully* from card events already stored in
   `matches.events_json`. Key players (tournament top scorers, or last-match
   scorer/assister) are emphasised. No mood/fitness, no new external API.

Mirrors the existing forecast pattern: deterministic backend → `FixtureDetail` fields →
new React component. Source brainstorm:
[`ck_plans/reports/260624-team-status-match-page-brainstorm.md`](../reports/260624-team-status-match-page-brainstorm.md).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Data layer (queries + models)](./phase-01-data-layer-queries-models.md) | Done |
| 2 | [Core logic (pure functions + API)](./phase-02-core-logic-pure-functions-api.md) | Done |
| 3 | [UI (component + wiring)](./phase-03-ui-component-wiring.md) | Done |

Execution order: 1 → 2 → 3 (data → core → ui). Phase 2 depends on Phase 1's models/query;
Phase 3 depends on Phase 2's API fields.

## Acceptance Criteria

- [ ] `compute_match_objective` returns a correct line for must-win, draw-enough,
      already-through, eliminated, and contention states (pytest).
- [ ] `compute_suspensions` is stateful: red card → next-match ban; 2 yellows → ban then
      **counter reset**; a player who served a ban is not re-flagged (pytest).
- [ ] `GET /api/fixtures/{id}` returns `home_status`/`away_status` for non-finished fixtures
      and `null` for finished ones.
- [ ] Team status renders on an upcoming and a live fixture; absent on finished.
- [ ] No fabricated fields (mood/fitness) anywhere in the response or UI.
- [ ] `frontend/public/CHANGELOG.md` updated; backend `pytest` + frontend `npm test` green.

## Constraints

- Deterministic / real-data only — honour the pipeline's fact-checking ethic.
- Reuse `standings_math` and stored `events_json`; **no** `/injuries` API call, **no** new
  external dependency.
- Group-stage scope only (knockout objectives + FIFA yellow-wipe handling are out of scope).

## Dependencies

No cross-plan dependencies. Standalone feature on existing data.

## Validation Log

### Session 1 — 2026-06-24

**Verification Results (Standard tier — Fact Checker + Contract Verifier)**
- Claims checked: 9 | Verified: 9 | Failed: 0 | Unverified: 0
- Confirmed: `FINISHED_STATUSES={"FT","AET","PEN"}` / `LIVE_STATUSES` (fixtures.py:39,43),
  `_MATCHES_PER_TEAM=3` / `_POINTS_WIN=3` (standings_math.py:16,18), `qualification_status` +
  `group_scenarios` (standings_math.py:107,166), card event shape `type="Card"
  detail="Yellow Card"` (seed_finished_match.py:47), `FixtureDetail` (api.ts:129), `MatchLive`
  slot props (page.tsx:69).
- **Correction:** the non-live/non-finished match state is `"preview"` (from `matchState` in
  lib/match.ts), not `"upcoming"`. Phase 3 wording updated accordingly.

**Decisions confirmed**
1. **Card semantics** — treat a `"Red Card"` OR `"Second Yellow card"` event as a direct
   next-match ban; separately track single `"Yellow Card"` accumulation (2 across matches →
   ban + counter reset). A `"Second Yellow card"` does NOT also feed the accumulation counter.
2. **Key player** — emphasise a flagged player if in the tournament top-scorers table OR
   they scored/assisted in the team's last match (uses existing data only).
3. **Objective depth** — reuse the simplified `group_scenarios` vocabulary (through / out /
   win-or-draw to stay top / must win); do NOT compute true draw-sufficiency (DRY, reuses
   tested logic, avoids new edge-case math).

**Whole-Plan Consistency Sweep:** re-read plan.md + all phase files post-propagation. No
unresolved contradictions. `PlayerStatus`/`TeamStatus` shapes, `objective_css` vocab, and
`FixtureDetail` fields consistent backend↔frontend. Recommendation: **proceed to implementation.**

### Session 2 — 2026-06-24 (implementation)

All three phases implemented and verified. Backend `pytest` 192 passed (17 new in
`test_availability.py`); frontend `vitest` 46 passed, `tsc` + `eslint` clean, `next build`
succeeds.

**Code-review finding (fixed):** `finished_group_matches_for_team` originally filtered on
`home_score IS NOT NULL`, but a live match also carries a score + partial event feed, so its
mid-match cards would have been replayed as settled bans. Re-gated on
`status IN ("FT","AET","PEN")` — matches the convention in `api/standings.py` and
`api/fixtures.py`. Objective computation reuses `standings_math.group_scenarios` keyed on
status + position (DRY, robust to note-string changes), a documented deviation from the
plan's per-group signature so WC2026 best-thirds advancement is honoured.

**Accepted (not actioned):** `group_scenarios` is computed once per side (twice per request);
negligible in-memory work over ~48 rows, left for clarity (YAGNI).
