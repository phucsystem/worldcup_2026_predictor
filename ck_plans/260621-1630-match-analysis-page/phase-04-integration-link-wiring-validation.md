---
phase: 4
title: "Integration: link wiring + validation"
status: complete
priority: P2
dependencies: [3]
effort: "S"
---

# Phase 4: Integration — link wiring + validation

## Overview

Wire the existing match cards across the app to link into `/match/[fixture_id]`, and validate all three states end-to-end against real fixtures. Small surface, easy to miss links.

## Requirements

- Functional: every place a match is shown links to its analysis page — home up-next + live banner, brief detail fixtures, fixtures list/knockout bracket, and (where a row maps to a fixture) standings recent results.
- Non-functional: links use `fixture_id`; no layout regression on the source pages; cards remain accessible (link has discernible label).

## Architecture

<!-- Updated: Validation Session 1 - card linking locked to explicit affordance (avoid nested <a>) -->
Each source component already has `fixture_id` in its data. Add an explicit **"Match analysis →"** link affordance per card with `href={\`/match/${fixture_id}\`}`. **Do not** wrap whole cards in an anchor — the live/next hero banners contain an inner "Watch live on SBS" link, and nesting `<a>` inside `<a>` is invalid HTML and breaks hydration. The explicit affordance is the single consistent pattern across plain fixture rows and hero banners alike.

## Related Code Files

- Modify: `frontend/components/next-match-card.tsx`, `frontend/components/live-match-card.tsx`, `frontend/components/fixture-list-item.tsx`, `frontend/components/fixture-row.tsx`, `frontend/components/knockout-bracket.tsx`, `frontend/components/fixtures-view.tsx` (whichever render fixture rows)
- Modify (if it lists fixtures): `frontend/app/brief/[date]/page.tsx` fixture references
- Reference: scan with `grep -rn "fixture_id" frontend/components frontend/app` to enumerate every match-bearing surface before editing.

## Implementation Steps

1. Enumerate match-bearing components (`grep -rn "fixture_id" frontend/`).
2. Add the explicit "Match analysis →" affordance to each (no whole-card anchors); keep `home`/`live` hero cards' existing behavior intact (don't break the live poll or the inner "Watch live" link).
3. Confirm provenance footer + data-source copy matches prototypes on the match page.
4. **Validation (manual, real data):**
   - Pick one fixture in each state (upcoming `NS`, in-play, finished `FT`) — use `backend/app/data/seed_live_match.py` to force a live fixture locally if none is in-play.
   - Verify: correct layout, events/timeline/goalscorers populate, forecast badge present, finished hit/miss badge computes, 404 on a bogus id.
   - Verify live page updates on the 30s poll (watch network tab / score change).
5. Run full suites: `cd backend && pytest`; `cd frontend && npm test && npm run build && npm run lint`.

## Success Criteria

- [ ] All match cards (home, brief, fixtures, knockout) link to `/match/[fixture_id]`.
- [ ] No regression on source pages; live banner poll still works.
- [ ] Manual check passes for upcoming, live, and finished fixtures + 404 path.
- [ ] Backend `pytest` + frontend `npm test`/`build`/`lint` all green.

## Risk Assessment

- **Missed link surface** — mitigated by the `grep` enumeration step before editing.
- **No live fixture available during the World Cup off-hours** — use `seed_live_match.py` to simulate; note this is dev-only seeding, not shipped data.
- **Hero card link vs. existing tap behavior** — verify the live poll and any existing nav still work after making the banner a link.
