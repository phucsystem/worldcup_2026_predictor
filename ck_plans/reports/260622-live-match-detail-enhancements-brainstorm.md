# Brainstorm — Live In-Progress Match Detail Enhancements

- **Date:** 2026-06-22
- **Branch:** `feat/live-match-events-update` (from `origin/main` @ 4898d098)
- **Mode:** Enhancement (current behavior is correct; add detail)
- **Next step:** `/ck:plan --tdd`

## Problem statement

The live match flow is already built end-to-end (live poller → `collect_live` → `matches.events_json` → `GET /api/fixtures/{id}` → `match-live.tsx` polling every 30s). The request is to **enrich what's shown** on the in-progress match page — specifically the live scorers and the Key-moments timeline — and to surface more of what's already (or could be) captured in the live poll. Latency stays as-is (~120s backend + 30s frontend); correctness/detail is the goal.

## Scope (agreed)

| ID | Enhancement | Layer | Data source |
|----|-------------|-------|-------------|
| A | Assists on timeline goal rows | Frontend | `MatchEvent.assist` (already polled) |
| B | Substitutions in↔out | Frontend | `player` + `assist` on `subst` (already polled) |
| C | VAR events (icon + label) | Frontend | `type="Var"`, `detail` (already polled) |
| D | Penalty / own-goal markers in banner strip | Frontend | `ScorerGoal.detail` (already polled) |
| E | "Just scored" live highlight | Frontend | event diff across polls |
| F | Live match statistics panel | Backend + Frontend | new `get_fixture_statistics` in `collect_live` |

Out of scope: G (player photos — events carry no photo URL; incomplete source, mostly falls back to initials), tournament top-scorers leaderboard, latency reduction / push transport.

## Touchpoints

- `frontend/components/match-timeline.tsx` — A, B, C (icon/typeLabel + row rendering)
- `frontend/lib/match.ts` — A, B, E pure helpers (unit-tested in `lib/match.test.ts`)
- `frontend/components/match-scorers-strip.tsx` — D
- `frontend/components/match-live.tsx` — E (diff + highlight), F (render stats panel)
- `frontend/lib/api.ts` — `FixtureDetail` already includes `statistics`; confirm types
- `backend/app/data/collect.py` `collect_live()` — F (fetch + overwrite stats per in-play fixture)
- `backend/app/api/fixtures.py` `normalize_statistics()` / `MatchStat` — reuse as-is for F

## Approach per item

**A — Assists on timeline.** Cards already show `assist`; timeline drops it. Add the assister to goal-row meta in `match-timeline.tsx`. Pure render.

**B — Substitutions in↔out.** Timeline shows only `player`. For `subst`, API-Football carries the second name in `assist`. Render "on ↔ off". **Verify on/off direction against a real stored `events_json`** before fixing copy — historically inconsistent in API-Football. Add a `lib/match.ts` helper so it's unit-tested.

**C — VAR events.** Currently a generic grey dot. Add a `Var` branch to `icon()` + `typeLabel()` surfacing `detail` ("Goal cancelled", "Penalty confirmed/overturned"). High live signal.

**D — Penalty/OG markers in strip.** `match-scorers-strip.tsx` shows only minutes, so a penalty looks like open play. Map `ScorerEntry.goals[].detail` (already available) to a compact marker (e.g. `(pen)`, `(o.g.)`), consistent with `goalLabel()` in `goalscorers.tsx`.

**E — "Just scored" highlight.** `MatchEvent` has no ID → key on `minute|extra|type|player|side`. Keep a ref of seen keys in `match-live.tsx`; on each poll, new keys get a transient highlight (CSS animation, auto-clears). Pure diff helper in `lib/match.ts`, unit-tested. Skip highlight on first render (initial SSR payload).

**F — Live statistics.** In `collect_live`, after events, also call `client.get_fixture_statistics(fixture_id)` per in-play fixture and store to `statistics_json`, **overwriting each poll** (the finished-match backfill guard does NOT apply to live). `FixtureDetail` already serves `statistics`; `normalize_statistics()` already shapes bars. Render the existing stats panel inside `match-live.tsx` (it currently omits stats). Per-fixture fetch is failure-guarded like the events fetch — a stats failure must not abort the score/status upsert.

## Risks / notes

- **B direction** is the only correctness unknown — pin with a real payload in the test, don't assume.
- **F doubles per-fixture live calls** (events + statistics). Acceptable given latency/cost deprioritized; only fires while a fixture is in the kickoff window.
- **F handoff to FT backfill:** once the live poll has stored stats, `backfill_finished_statistics` will skip that fixture (guarded on "has stats"). Final stats = last live poll's, which is fine. Note, don't fight it.
- **E** must not flash the whole timeline on first paint — only events unseen in the prior poll.

## Acceptance criteria

- Timeline shows assister on goals (A), both players on subs (B), and a distinct VAR row (C).
- Banner strip distinguishes penalty/own-goal from open-play goals (D).
- A goal/event arriving on a live poll is briefly highlighted; nothing flashes on initial load (E).
- During an in-play match, a live stats panel (possession/shots/xG/corners) appears and refreshes on the poll; a stats fetch failure never breaks score updates (F).
- New/extended pure logic in `lib/match.ts` covered by `lib/match.test.ts`; `collect_live` stats path covered backend-side.

## Validation

- Frontend: `lib/match.test.ts` for diff/sub/scorer helpers; component render checks.
- Backend: unit test `collect_live` stores+overwrites stats for in-play fixtures and survives a stats-fetch exception.
- Existing e2e (Robot Framework) for the match page should stay green.
