---
phase: 4
title: Frontend
status: completed
priority: P1
dependencies:
  - 3
effort: ''
---

# Phase 4: Frontend

## Overview

Render the two new sections on the finished branch of `/match/[fixture_id]`:
**The verdict** (`.analysis-note`) and **Match stats** (`.stat-bars`), in the
S-10 order, hiding each when its data is absent. Port the needed CSS verbatim.

## Requirements

- Functional: verdict block + stats bars appear for a fixture that has them;
  neither renders when absent.
- Non-functional: match S-10 markup/classes; respect the modified-Next.js note
  (`frontend/AGENTS.md` — read `node_modules/next/dist/docs/` before route edits);
  no horizontal scroll; reduced-motion safe.

## Architecture

- `lib/api.ts`: add `MatchStat` interface + `statistics: MatchStat[]`, `verdict:
  string | null`, `verdict_model: string | null` to `FixtureDetail` (mirror backend).
- New component `frontend/components/match-stats.tsx`: renders `.stat-bars`
  (`.sb-row`/`.sb-top`/`.sb-val`/`.sb-track`/`.sb-fill home|away`) from
  `statistics`; the `lead` class on the higher side; returns `null` when empty.
- Verdict: render the `.analysis-note` block (`.an-eyebrow` "The verdict" + `<p>`)
  inline in `page.tsx` (or a tiny `match-verdict.tsx`) when `fixture.verdict`.
- `page.tsx` finished branch — insert in S-10 order:
  hero → **verdict** → forecast → forecast-vs-result → timeline → goalscorers →
  **match stats** → stakes → footer. Extend the footer provenance to add
  `narrative: {verdict_model}` when a verdict is present.
- `globals.css`: port `.stat-bars`, `.sb-*`, `.analysis-note`, `.an-eyebrow`
  **verbatim** from `prototypes/components.css` (predecessor's porting decision).
- Optional pure helper in `lib/match.ts` only if any client-side derivation is
  needed (percentages already come from the API — likely none).

## Related Code Files
- Modify: `frontend/lib/api.ts` (types)
- Create: `frontend/components/match-stats.tsx` (+ optional `match-verdict.tsx`)
- Modify: `frontend/app/match/[fixture_id]/page.tsx` (finished branch + footer)
- Modify: `frontend/app/globals.css` (port stat-bar + analysis-note classes)

## Implementation Steps

1. **(TDD, only if a `lib/` helper is added)** Write the vitest first; otherwise
   no unit test (JSX is not unit-tested in this repo).
2. Add the new `FixtureDetail` fields to `lib/api.ts`.
3. Port the CSS class families into `globals.css`.
4. Build `MatchStats` (hide when empty); add the verdict block.
5. Wire both into the finished branch in S-10 order; extend footer provenance.
6. `npm run build` + `eslint`; visually verify against `s10-match-final.html`.

## Success Criteria
- [ ] Verdict `.analysis-note` renders when present, hidden when null.
- [ ] `MatchStats` renders the `.stat-bars` for a fixture with stats, hidden when empty.
- [ ] Section order matches S-10; footer credits the verdict model when present.
- [ ] `npm run build` and `eslint` are clean.

## Risk Assessment
- Modified Next.js: confirm server-component data flow (already `force-dynamic`)
  before adding components — read the bundled docs first per `AGENTS.md`.
- CSS drift: port verbatim rather than re-deriving Tailwind utilities, matching
  how `next-match`/`stake-card` already live in `globals.css`.
