---
phase: 2
title: "Core logic (pure functions + API)"
status: done
effort: ""
---

# Phase 2: Core logic (pure functions + API)

## Overview

Write the deterministic pure functions that produce a team's match objective and player
availability, test them first (TDD), then surface them on `GET /api/fixtures/{id}` via new
`home_status` / `away_status` fields populated only for non-finished fixtures.

## Requirements

- Functional:
  - `compute_match_objective(...)` → one objective line + css token per team for THIS fixture.
  - `compute_suspensions(team_matches_in_order, *, key_names)` → `list[PlayerStatus]` split
    into suspended vs at-risk, with `key_player` flagged.
  - Endpoint returns `TeamStatus` per side for upcoming/live; `None` for finished.
- Non-functional: pure functions (no I/O) live in a unit-tested module; endpoint stays a
  single DB read path; zero external calls.

## Architecture

- **New module** `backend/app/data/availability.py` (pure, no I/O — like `standings_math.py`):

  ```python
  def compute_match_objective(group_rows, team, *, group_complete) -> tuple[str, str]:
      # Reuse standings_math.qualification_status / group_scenarios vocabulary.
      # Map (status, position) -> human line + css:
      #   qualified            -> ("Already through — playing for seeding", "qualified")
      #   eliminated           -> ("Eliminated — pride only", "out")
      #   contention pos 1-2    -> ("Win or draw to stay top", "contention")
      #   contention pos 3-4    -> ("Must win to advance", "contention")
      # Returns ("", "") when group_rows is empty (knockout / unknown) so the
      # objective block can be omitted.
  ```

  ```python
  def compute_suspensions(team_matches_in_order, team, *, key_names) -> list[PlayerStatus]:
      # Replay matches oldest->newest. For each card event for `team`:
      #   - "Red Card" OR "Second Yellow card" -> DIRECT next-match ban (reason "red-card").
      #         Does NOT feed the yellow-accumulation counter.
      #   - "Yellow Card" -> increment per-player single-yellow count; on the 2nd ->
      #         suspended next match (reason "yellow-accumulation"), then RESET count to 0.
      # A player carrying exactly 1 single yellow after the latest match -> at_risk ("one-yellow").
      # A player banned as a result of the LATEST match -> suspended (it's served in THIS fixture).
      # key_player = player name in key_names (top scorers ∪ last-match scorers/assisters).
      # Decisions locked in Validation Session 1 (see plan.md).
  ```

  - Card events are parsed from each match dict's `events_json` (type == "Card",
    detail in {"Yellow Card", "Red Card", "Second Yellow card"}), filtered to the team.
  - **Statefulness is the crux:** a ban is served in the match immediately after it is
    incurred, then the counter resets — a player must never appear suspended two matches
    running for the same accumulation. Replay order = kickoff order from Phase 1's query.

- **API wiring** in `backend/app/api/fixtures.py`:
  - Add `home_status: Optional[TeamStatus]` / `away_status: Optional[TeamStatus]` to
    `FixtureDetail`.
  - In `get_fixture`, when the fixture is **not finished** (status not in
    `FINISHED_STATUSES`):
    - load standings group rows for `fixture.group_name`,
    - call `repository.finished_group_matches_for_team` for each side,
    - build `key_names` from `top_scorers_table` (team match) ∪ each team's last-match
      goal/assist events,
    - assemble `TeamStatus(objective=..., unavailable=..., at_risk=...)` per side.
  - Finished fixtures: leave both `None` (keeps the finished view unchanged).

## Related Code Files

- Create: `backend/app/data/availability.py`
- Create: `backend/tests/test_availability.py`
- Modify: `backend/app/api/fixtures.py` (`FixtureDetail` model + `get_fixture` body)
- Reference: `backend/app/data/standings_math.py` (`qualification_status`, `group_scenarios`),
  `backend/app/data/repository.py` (`top_scorers_table`, Phase 1 helper)

## Implementation Steps

1. **TDD first** — write `test_availability.py` covering:
   - objective: must-win (pos 3-4 contention), draw-enough (pos 1-2 contention), through,
     eliminated, empty group_rows → empty objective.
   - suspensions: clean player (no flag); single yellow → at_risk; two yellows across two
     games → suspended in the 3rd, then **not** suspended afterwards; red card → suspended
     next match only; **"Second Yellow card" → direct ban, not double-counted into
     accumulation**; key_player flag set when name in `key_names`.
2. Implement `availability.py` to pass the tests; keep it pure (accept already-loaded dicts).
3. Extend `FixtureDetail` with the two optional fields.
4. Wire `get_fixture`: gather standings rows + per-team prior matches + key names, assemble
   `TeamStatus` for non-finished fixtures only.
5. Run `pytest backend/tests/test_availability.py` then the full backend suite.

## Success Criteria

- [ ] All `test_availability.py` cases pass, including the ban-then-reset accumulation case.
- [ ] `GET /api/fixtures/{id}` returns populated `home_status`/`away_status` for an
      upcoming/live fixture and `null` for a finished one.
- [ ] Existing fixture/standings tests stay green; no new external calls introduced.

## Risk Assessment

- **Accumulation over-flagging (primary):** mitigated by replaying in kickoff order and
  resetting the counter after a served ban; explicit pytest case locks this.
- **Name-only player identity:** API events give player name strings, no stable id. Accept
  for display; `key_names` matching is name-based (documented limitation).
- **Group rows availability:** if standings lack the group (early tournament), objective
  returns empty and the block is omitted — handled, not an error.
