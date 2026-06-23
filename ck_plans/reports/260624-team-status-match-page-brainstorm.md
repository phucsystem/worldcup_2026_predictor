# Brainstorm — Team Status on Match Page (objective + availability)

**Date:** 2026-06-24
**Mode:** standard (no --html / --wiki)
**Surface:** `/match/[fixture_id]` — upcoming + live states only
**Status:** Approved → handed to /ck:plan

---

## 1. Problem statement

For upcoming and in-progress matches, the match analysis page shows forecast %, recent
form, and the group table, but never states **what each team must achieve in this specific
game**, nor **which players are unavailable**. Users can't quickly see "Team A must win to
survive" or "their top scorer is suspended after a red card last game."

## 2. Requirements (locked)

- **Expected output:** A "Team status" section on `/match/[fixture_id]`, rendered for
  `upcoming` and `live` fixtures, with two parts per team:
  1. **Match objective** — one deterministic line on what the team needs from this game.
  2. **Availability** — fact-based player flags (suspended / one booking from a ban),
     with key-player emphasis when the flagged player is a tournament top scorer or
     scored/assisted in the team's last match.
- **Acceptance criteria:**
  - Objective line is correct for representative group-stage states (must-win, draw-enough,
    already-through, eliminated, scenario-dependent).
  - Suspension flags computed *statefully* (2 yellows → ban → counter resets; red card →
    next-match ban) — no over-flagging of players who already served a ban.
  - Section appears on upcoming + live, absent on finished.
  - No fabricated data: mood/fitness excluded entirely.
- **Scope boundary (OUT):** player mood/fitness, API-Football `/injuries` endpoint,
  home-page cards, fixtures-list surfacing, knockout-stage objectives, live recomputation
  of the objective during play.
- **Non-negotiable constraints:** deterministic / real-data only (honours the pipeline's
  fact-checking ethic); reuse existing standings + card-event data; no new external API.
- **Touchpoints:** `backend/app/data/standings_math.py`, `backend/app/data/repository.py`,
  `backend/app/api/fixtures.py` (`FixtureDetail`), `frontend/app/match/[fixture_id]/page.tsx`,
  new `TeamStatus` frontend component, new `backend/app/data/availability.py`.

## 3. Decisions (user-confirmed)

| Decision | Choice |
|---|---|
| Player condition | **Real data only** — drop mood/fitness |
| Surface area | **Match page, upcoming + live only** |
| Stakes logic | **Extend existing qualification logic** (standings_math) |
| Card/suspension source | **Derive from stored card events** — no new API |
| Live behaviour | **Static pre-kickoff snapshot** (no live recompute) |

## 4. Approaches evaluated

| Approach | Pros | Cons | Verdict |
|---|---|---|---|
| **A. Backend pure functions + FixtureDetail fields + new component** | Mirrors existing `forecast.py → forecast_json → MatchForecast → ForecastCard`; deterministic logic unit-tested in pytest like `standings_math`; card history already server-side; thin client | New API fields + repository query for each team's prior matches | **CHOSEN** |
| B. Frontend compute in `lib/` | Matches `stakes.ts`/`results.ts` pattern | Client lacks other teams' events → ship far more data per request; suspension math harder to test | Rejected |

## 5. Recommended solution (Approach A)

- **New pure module** `backend/app/data/availability.py`:
  - `compute_suspensions(team_matches_in_order) -> list[PlayerStatus]` — stateful replay of
    card events; emits `suspended` (red card or 2nd yellow last game) and `at_risk`
    (sitting on one yellow). Counter resets after a served ban.
  - `compute_match_objective(group_rows, remaining_fixtures, fixture) -> str` — extends the
    existing qualification logic to a per-team, per-match objective line.
- **API:** extend `FixtureDetail` with optional `home_status` / `away_status`:
  `{ objective: str, unavailable: [PlayerStatus], at_risk: [PlayerStatus] }`. Populated only
  for non-finished fixtures.
- **Repository:** query each team's prior group-stage matches (with events) for the
  availability computation.
- **Frontend:** new `TeamStatus` component, slotted into the upcoming + live branches of the
  match page next to `QualificationStakes`; reuses existing card/badge styling. Live state
  shows the static snapshot.
- **Key-player emphasis:** cross-reference flagged player names against `TopScorer` data and
  the team's last-match goal/assist events.

## 6. Risks & mitigations

- **Yellow-accumulation correctness (primary):** must replay matches in order and reset the
  counter after a served ban; naive totals over-flag. → dedicated pure function with pytest
  cases covering ban-then-reset.
- **Player identity:** API-Football events identify players by name string (no stable id
  join). Adequate for display; documented limitation. Key-player match is name-based.
- **FIFA yellow-wipe rule:** yellows are cleared after the quarter-finals; group-stage-only
  scope sidesteps this for now (knockout objectives are out of scope).

## 7. Success metrics / validation

- pytest unit tests for `compute_suspensions` (red-card ban, 2-yellow ban, ban-then-reset,
  clean player) and `compute_match_objective` (must-win, draw-enough, through, eliminated,
  scenario-dependent).
- Manual QA: Team status renders on an upcoming + a live fixture, absent on finished.
- No fabricated fields present in API response.

## 8. Next steps

1. `/ck:plan` — phase the implementation (data → core → ui), TDD-friendly given the pure
   functions.
2. Update `frontend/public/CHANGELOG.md` (CI gate) when the PR is raised.
