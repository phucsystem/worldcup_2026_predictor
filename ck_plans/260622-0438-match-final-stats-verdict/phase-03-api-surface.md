---
phase: 3
title: API surface
status: completed
priority: P1
dependencies:
  - 1
  - 2
effort: ''
---

# Phase 3: API surface

## Overview

Expose statistics + verdict through `FixtureDetail`: a pure shaping function maps
the raw statistics payload into ordered, percentage-bearing `MatchStat` rows, and
the verdict text/model are passed through. All percentage math is in Python.

## Requirements

- Functional: `GET /api/fixtures/{id}` returns `statistics: list[MatchStat]` and
  `verdict` / `verdict_model` on `FixtureDetail`.
- Non-functional: shaping is a pure function (unit-tested); missing stat types
  are omitted (no zero-fill); empty payload → empty list (drives Phase 4 hiding).

## Architecture

- `MatchStat` Pydantic model: `{label, home, away, home_pct, away_pct}`. Values
  are numbers or display strings as the payload provides; `*_pct` are the bar
  widths computed in Python (`home/(home+away)`, guarded against div-by-zero;
  possession passes through if already a percentage).
- `normalize_statistics(raw, home_team, away_team) -> list[MatchStat]` beside
  `normalize_events` (`fixtures.py:128`): map the API stat labels to the S-10 set
  (Ball Possession, Total Shots, Shots on Goal, Corner Kicks, expected_goals) in
  the prototype's display order; **omit** any stat absent from the payload.
- Extend `get_fixture` (`fixtures.py:339`) to read `statistics_json` + verdict
  columns and populate the new `FixtureDetail` fields.

## Related Code Files
- Modify: `backend/app/api/fixtures.py` (`MatchStat`, `normalize_statistics`, `FixtureDetail`, `get_fixture`)
- Create tests: `backend/tests/test_fixture_statistics_shaping.py`

## Implementation Steps

1. **(TDD)** Write `normalize_statistics` tests: correct label mapping + order;
   `home_pct`/`away_pct` sum to ~100 and round sensibly; possession-as-percent
   handled; a missing stat type is omitted; empty/None input → `[]`;
   div-by-zero (both 0) does not crash.
2. Add `MatchStat`; implement `normalize_statistics`.
3. Add `statistics`, `verdict`, `verdict_model` to `FixtureDetail`; populate in `get_fixture`.
4. Run `pytest`.

## Success Criteria
- [ ] `normalize_statistics` is pure, ordered, omits missing stats, no zero-fill; unit-tested.
- [ ] `FixtureDetail` carries `statistics`, `verdict`, `verdict_model`.
- [ ] `GET /api/fixtures/{id}` returns the new fields for a stats+verdict fixture and empty/null for one without.
- [ ] `pytest` passes (tests first).

## Risk Assessment
- API stat label strings may differ from assumptions — drive the label map from
  the real payload captured in Phase 1, and keep the map in one place so adding a
  stat later is a one-line change.
