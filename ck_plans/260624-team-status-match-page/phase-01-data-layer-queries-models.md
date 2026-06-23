---
phase: 1
title: "Data layer (queries + models)"
status: done
effort: ""
---

# Phase 1: Data layer (queries + models)

## Overview

Introduce the Pydantic models for player/team status and a repository helper that loads a
team's prior group-stage matches (with `events_json`) needed to compute suspensions. No
business logic yet — just typed data plumbing the core phase will consume.

## Requirements

- Functional: provide `PlayerStatus` and `TeamStatus` Pydantic models; provide a query that,
  given a team name, returns that team's finished group-stage matches in kickoff order with
  their raw card events available.
- Non-functional: no new external API; query reads the existing `matches_table`; pure-ish
  (single DB read), no LLM, no network.

## Architecture

- **Models** live in `backend/app/data/models.py` (alongside `Match`, `TopScorer`):
  ```python
  class PlayerStatus(BaseModel):
      player: str
      reason: str          # "red-card" | "yellow-accumulation" | "one-yellow"
      status: str          # "suspended" | "at_risk"
      key_player: bool = False   # top scorer, or scored/assisted last match

  class TeamStatus(BaseModel):
      objective: str               # e.g. "Must win to advance"
      objective_css: str           # reuse group_scenarios css vocab: "qualified"|"out"|"contention"
      unavailable: list[PlayerStatus] = []
      at_risk: list[PlayerStatus] = []
  ```
- **Repository helper** in `backend/app/data/repository.py`:
  ```python
  def finished_group_matches_for_team(session, team: str) -> list[dict]:
      # rows where (home_team == team OR away_team == team)
      #   AND group_name IS NOT NULL          # group stage only
      #   AND home_score IS NOT NULL          # finished/has result
      # ORDER BY kickoff_utc
      # return _row_to_dict-shaped dicts incl. events_json
  ```
  Card events are read from each row's `events_json` (already stored). The shaping mirrors
  the existing `_row_to_dict` in `fixtures.py` but must include `events_json`.

## Related Code Files

- Modify: `backend/app/data/models.py` (add `PlayerStatus`, `TeamStatus`)
- Modify: `backend/app/data/repository.py` (add `finished_group_matches_for_team`)
- Reference (no change): `backend/app/api/fixtures.py` (`_row_to_dict`, `matches_table` import)

## Implementation Steps

1. Add `PlayerStatus` and `TeamStatus` to `models.py` with the fields above.
2. Add `finished_group_matches_for_team(session, team)` to `repository.py`, selecting from
   `matches_table` with the filters above, ordered by `kickoff_utc`, returning dicts that
   include `events_json`, `home_team`, `away_team`, `home_score`, `away_score`, `kickoff_utc`.
3. Keep the helper free of business logic — it only loads and shapes rows.

## Success Criteria

- [ ] `PlayerStatus` and `TeamStatus` import cleanly and validate.
- [ ] `finished_group_matches_for_team` returns only finished group-stage matches for the
      team, in kickoff order, with events accessible.
- [ ] No changes to existing endpoints or external calls; existing `pytest` stays green.

## Risk Assessment

- Low risk: additive models + one read query. Main gotcha is ensuring `events_json` is
  carried through (the existing `_row_to_dict` omits it) — verify the helper includes it.
