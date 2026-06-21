# Finished Match Page — Stats + Verdict (S-10 v2)

**Date:** 2026-06-22
**Plan:** `ck_plans/260622-0438-match-final-stats-verdict`
**Branch:** `fix/goalscorer-test-shape`

## What

Closed the two sections the finished match page (`/match/[fixture_id]`) was still
missing versus the `s10-match-final.html` prototype:

1. **Match stats** — real possession/shots/SoT/xG/corners from API-Football
   `/fixtures/statistics`.
2. **The verdict** — a 1-2 sentence neutral recap narrated by DeepSeek from a
   pre-computed fact bundle.

This is the v2 follow-up to the completed `260621-1630-match-analysis-page` plan,
which had explicitly deferred both to out-of-scope v1.

## How

Both follow the existing `events_json` vertical slice verbatim, keeping the change
DRY: collector → `matches` JSON/text column → Python-normalized `FixtureDetail`
field → React component, populated by a guarded once-only on-finish backfill.

- **Migration 0007** adds `statistics_json`, `verdict_text`, `verdict_model`.
- **`upsert_matches`** got the same conditional-write clobber-guard as `events_json`
  (the daily collect carries no stats/verdict, so unconditional writes would wipe
  backfilled data).
- **Verdict** lives in `app/pipeline/verdict.py`: a pure `build_match_verdict_facts`
  (the only thing handed to the model — own-goal credit reversal handled) plus
  `generate_match_verdict` reusing the editor node's `make_structured_client` +
  retry-twice + keep-last-good contract. The prompt forbids inventing any number.
- **Stats shaping** computes bar percentages in Python and omits stat types absent
  from the payload (no zero-fill).

## Decisions

- **Verdict tone:** neutral factual recap (user choice) — lowest fabrication risk.
- **Verdict source:** LLM from a structured fact bundle, not free text — keeps the
  no-fabrication principle intact while still reading naturally.
- **Stats incl. xG:** viable because the project is on a paid API-Football plan
  (README/architecture docs corrected from the old free-tier framing).

## Validation

- Backend pytest **141 passed** (+27 new across 3 files); frontend vitest **34**;
  `npm run build` + TS clean; eslint clean on changed files.
- code-reviewer: **no blocking issues**; one Low hardening fix applied
  (`normalize_statistics` falls back to payload order if *either* team name fails
  to match, not only both — avoids a one-sided fabricated "0").
- End-to-end verified via `seed_finished_match.py` on a seeded row: 5 stat bars
  (percentages sum to 100), verdict + model present; clear → graceful degradation.

## Outstanding

- **Manual gate (needs API spend):** one real collect against a finished season-2026
  fixture to confirm the live `/fixtures/statistics` payload maps as expected;
  `_STAT_LABELS` is the only thing that might need adjustment if labels differ.
