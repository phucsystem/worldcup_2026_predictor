# Live In-Progress Match Detail Enhancements — Implementation

**Date**: 2026-06-22 09:30
**Severity**: Low (feature complete, code-side acceptance criteria met)
**Component**: Frontend (Next.js match page) + Backend (live poller `collect_live`)
**Status**: Resolved (code) — match-page e2e + live-payload subst check pending
**Commit**: `db34d60d` on `feat/live-match-events-update`

## What Happened

Six enhancements to the already-working live match flow (live poller → `collect_live` →
`matches.events_json` → `GET /api/fixtures/{id}` → `match-live.tsx` 30s poll). Brainstorm → plan
(`--tdd`) → cook. Latency left as-is (~120s backend + 30s frontend); the work was rendering detail the
poll already carries, plus one backend addition (live stats).

- **A** assister on timeline goal rows · **B** substitutions `on ↔ off` · **C** VAR rows get a dedicated
  icon + label from `detail` — all in `match-timeline.tsx`, driven by new pure helpers.
- **D** penalty/own-goal markers `(pen)`/`(o.g.)` in the banner scorers strip (`match-scorers-strip.tsx`).
- **E** "just-scored" highlight: events newly arrived on a poll briefly flash. `seenKeys` ref seeded from
  the initial SSR payload so the first paint flashes nothing; reduced-motion gets a static accent instead.
- **F** live statistics: added a guarded `get_fixture_statistics` call in `collect_live`'s per-fixture
  loop (overwrite each poll, no once-only guard), failure-isolated so a stats error never drops the
  score/status/events upsert. Frontend reuses the existing `<MatchStats>` panel — no new infra.

## The Brutal Truth

Most of this was rendering, not engineering — the events feed was already in the 30s poll, so A–E
touched no data layer. F looked like the big item but `normalize_statistics`, `MatchStat`, and
`FixtureDetail.statistics` already existed from the finished-match work; the only real backend change was
~7 lines in `collect_live`. The discipline that mattered was keeping F's stats fetch in its own
try/except so it can't take down the events/score upsert.

The one genuine unknown — API-Football's `subst` direction (`player`=on vs `assist`=off) — could not be
verified against a real payload because Docker/Postgres was down locally. Followed the documented
convention (corroborated by the repo's own `test_substitution_event` fixture) and flagged it in a code
comment. Cheap to eyeball on the first live substitution; worst case the two names swap, no crash.

Code review found no blockers and confirmed the two paths I expected to be buggy (F guard, E first-paint
lifecycle) were correct. Applied its two correctness fixes: broadened `eventKey` to include `detail` +
`team` (player-less VAR/sub events at the same minute were colliding and missing their highlight) and
keyed timeline rows by event identity instead of array index. Skipped one nit (clearing `freshKeys`
after the flash) per KISS — the lingering accent only shows under reduced-motion.

## Technical Details

- `eventKey` = `minute|extra|type|detail|player|team|side`; `freshEventKeys(prevKeys, events)` diffs
  against the accumulated seen-set, so an event can never be "fresh" twice — the flash re-triggers
  correctly despite shared timeline rows.
- `subOnOff` and the timeline `assist` field are pure and unit-tested; `TimelineRow` gained `assist` +
  `team`.
- `collect_live` stats path covered by a new `backend/tests/test_collect_live.py` (fake client + fake
  session, no DB): stores stats, re-fetches every poll, survives a stats exception, ignores unknown
  fixtures.
- Tests: frontend **42/42 vitest**; backend **147 passed** (5 failures are pre-existing DB-connection
  errors — Postgres down — identical on the clean base). `tsc` + eslint clean on changed files.

## Remaining (manual / CI)

1. Run the Robot Framework match-page e2e (needs the full Docker stack — down locally this session).
2. Eyeball the first live substitution to confirm `player`=on / `assist`=off in production data.
