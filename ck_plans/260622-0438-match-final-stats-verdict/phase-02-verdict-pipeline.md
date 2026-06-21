---
phase: 2
title: Verdict pipeline
status: completed
priority: P1
dependencies:
  - 1
effort: ''
---

# Phase 2: Verdict pipeline

## Overview

Generate a one-line per-match **verdict** with DeepSeek, narrated strictly from a
pre-computed fact bundle (score, scorers + minutes, cards, standings delta,
qualification outcome). Persist keep-last-good into `verdict_text`/`verdict_model`.

## Requirements

- Functional: build a structured fact bundle from stored match + standings data;
  ask DeepSeek to narrate only those facts in 1-2 sentences; persist on success.
- Non-functional: no invented numbers; keep-last-good (never overwrite a stored
  verdict with empty); failure logs + skips, never aborts the collect.

## Architecture

- **Pure fact-bundle builder** (testable, no LLM): `build_match_verdict_facts(match, group_rows) -> dict`
  in a new `backend/app/pipeline/verdict.py`. Inputs: final score, normalized
  scorers (reuse event normalization), red/yellow cards, the group standings
  delta + qualification status. Output: a compact structured dict — the only
  thing handed to the model.
- **Generation**: `make_structured_client(Verdict)` (pattern from
  `nodes_editor.py:31`), a `Verdict` Pydantic model `{text: str}`, and a
  constrained system prompt in `prompts.py` reusing the existing
  *"Do NOT invent statistics, standings positions, or scores"* rule, instructed
  to narrate ONLY the supplied facts in ≤2 sentences.
- **Trigger**: called from the same on-finish backfill block in `collect.run`
  (after events + stats are present for the match), for finished matches whose
  `verdict_text` is null. Persist `verdict_text` + `verdict_model` (the
  deepseek-chat model id) only when the call succeeds and returns non-empty text.
- Honor the existing graph-level "no outer retry re-pays DeepSeek" lesson
  (`ck_docs/journal/2026-06-19…`): one attempt per match per run, failures surface to logs.

## Related Code Files
- Create: `backend/app/pipeline/verdict.py` (fact builder + generate + persist)
- Modify: `backend/app/pipeline/prompts.py` (verdict system prompt)
- Modify: `backend/app/data/collect.py` (invoke verdict generation in on-finish block)
- Create tests: `backend/tests/test_match_verdict.py`

## Implementation Steps

1. **(TDD)** Write `build_match_verdict_facts` tests: correct winner/margin,
   scorers grouped with minutes, standings delta + qualification status present,
   nothing fabricated (only fields derivable from inputs appear).
2. **(TDD)** Write a keep-last-good persistence test: empty/failed generation
   does not null an existing `verdict_text`; success stores text + model.
3. Implement the fact builder (pure).
4. Add the `Verdict` model + constrained prompt; implement `generate_match_verdict(facts)`.
5. Wire generation into the `collect.run` on-finish block (guarded, after Phase 1 stats).
6. Run `pytest`.

## Success Criteria
- [ ] `build_match_verdict_facts` is pure and unit-tested; emits only derivable facts.
- [ ] Verdict prompt forbids invention and constrains to ≤2 sentences from supplied facts.
- [ ] Keep-last-good: failed/empty generation never clears a stored verdict; unit-tested.
- [ ] Verdict generation failure logs + skips without aborting the collect.
- [ ] `pytest` passes (tests written first).

## Risk Assessment
- This is the only generative surface over match data. The structured fact
  bundle (not free text) + no-invention prompt + visible provenance (Phase 4)
  are the guardrails — do not relax them. If verdict quality is poor, prefer
  tightening the prompt over feeding richer free-text inputs.
