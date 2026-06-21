---
phase: 5
title: Integration & validation
status: completed
priority: P2
dependencies:
  - 4
effort: ''
---

# Phase 5: Integration & validation

## Overview

End-to-end validation against a seeded finished match with statistics + verdict,
confirmation of graceful degradation, full-suite green, and doc reconciliation.

## Requirements

- Functional: a real/seeded finished fixture renders verdict + stats correctly;
  a fixture missing either degrades cleanly.
- Non-functional: full backend + frontend suites, build, and lint pass; docs
  reflecting data-source/columns are accurate.

## Architecture

- Extend the existing dev seed (the predecessor's `seed_live_match.py` or
  equivalent finished-match seed) to include a `statistics_json` payload and a
  stored `verdict_text`/`verdict_model`, so the finished page can be validated
  without a live API call.
- Manual/scripted check of `/match/[fixture_id]` for: (a) stats + verdict present,
  (b) stats absent → no stats section, (c) verdict absent → no verdict block.

## Related Code Files
- Modify: backend dev seed script (add statistics + verdict to a finished fixture)
- Modify (docs): `ck_docs/system-architecture.md` env table note if a
  statistics/verdict column or `/fixtures/statistics` usage should be documented
- Verify (no change expected): `README.md`, `prototypes/README.md` (already
  updated to reflect the paid plan + stats availability this session)

## Implementation Steps

1. Apply migration `0007` on the dev DB; seed a finished fixture with stats + verdict.
2. Run the full backend `pytest` and frontend `vitest` suites; `npm run build` + `eslint`.
3. Validate the three render states (full / no-stats / no-verdict) on the page.
4. Trigger a real collect against one finished season-2026 fixture to confirm the
   live `/fixtures/statistics` shape matches the Phase 1 fixture + Phase 3 mapping;
   adjust the label map if reality differs.
5. Reconcile docs (system-architecture env/columns) with the shipped change.

## Success Criteria
- [ ] Seeded finished fixture renders verdict + all available stat bars per S-10.
- [ ] No-stats and no-verdict fixtures degrade with no empty scaffolding.
- [ ] Full `pytest` + `vitest` pass; `npm run build` + `eslint` clean.
- [ ] One real collect confirms the live statistics payload maps correctly.
- [ ] Docs reconciled; no stale free-tier/data-availability claims remain.

## Risk Assessment
- The live payload may reveal label/shape mismatches not captured by the test
  fixture — Step 4 is the real-data gate; treat a mismatch as a Phase 3 label-map
  fix, not a redesign.
- Backfilling verdicts/stats for already-finished matches: the guarded on-finish
  pass only covers matches finishing after deploy. If historical matches must be
  populated, an optional one-shot admin reprocess (clear-null-and-rerun) can be
  added — flagged, not built, unless the user asks.
