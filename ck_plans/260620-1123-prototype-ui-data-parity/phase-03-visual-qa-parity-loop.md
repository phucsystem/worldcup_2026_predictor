---
phase: 3
title: "Visual QA Parity Loop"
status: complete
priority: P1
effort: "1d"
dependencies: [2]
---

# Phase 3: Visual QA Parity Loop

## Overview
Prove pixel-perfect parity by screenshotting the running app against each prototype at desktop + mobile widths, diffing, and fixing drift until each of the 6 screens matches. This phase is the acceptance test for fidelity (verification, not unit tests).

## Requirements
- **Functional:** for each of 6 screens, app screenshot matches prototype screenshot at desktop (1280px) and mobile (390px).
- **Non-functional:** no horizontal body scroll (prototype invariant); wide tables scroll inside their container; reduced-motion parity.

## Architecture
- Serve prototypes as static HTML (`prototypes/s0X-*.html`) and run the app (docker-compose, backend + frontend) with collected real data.
- Capture screenshots with `claude-in-chrome` at both widths for prototype and app.
- Compare side-by-side; log concrete drift (spacing, color, weight, radius, alignment, motion); fix in `frontend/` (loops back into Phase 2 files); re-shoot until matched.
- Track per-screen sign-off in a checklist.

## Related Code Files
- Modify (as drift dictates): `frontend/components/*`, `frontend/app/**/page.tsx`, `frontend/app/globals.css`
- Reference: all `prototypes/s0X-*.html`, `prototypes/components.css`, `prototypes/styles.css`
- Create (optional): `ck_plans/260620-1123-prototype-ui-data-parity/visuals/` for before/after captures

## Implementation Steps
1. Bring up backend + Postgres + frontend; confirm real data renders.
2. Serve prototypes locally (static file server or file:// per asset rules).
3. Per screen (S-01…S-06): screenshot prototype + app at 1280px and 390px.
4. Diff; record drift list per screen.
5. Fix highest-impact drift first (layout → spacing → color/weight → motion); re-shoot.
6. Repeat until each screen matches at both widths; mark sign-off.
7. Confirm no-horizontal-scroll + reduced-motion across all screens.

## Success Criteria
- [ ] All 6 screens signed off at desktop + mobile (screenshot diff).
- [ ] No horizontal body scroll on any screen; wide tables scroll internally.
- [ ] Data-thin elements (sparkline/form) degrade gracefully on real data.
- [ ] `next build` still green after fixes.

## Per-screen sign-off
- [ ] S-01 Home (`/`)
- [ ] S-02 Brief detail (`/brief/[date]`)
- [ ] S-03 Standings (`/standings`)
- [ ] S-04 Archive (`/archive`)
- [ ] S-05 Fixtures (`/fixtures`)
- [ ] S-06 Changelog (`/changelog`)

## Risk Assessment
- **Font rendering / antialiasing** differs slightly between static HTML and Next runtime — accept sub-pixel differences; chase structural/spacing/color parity, not literal pixel hashes.
- **Real data ≠ prototype mock content** — parity is about layout/style fidelity, not identical text/teams. Judge structure, not content.
- **Scope creep in the loop** — cap drift-fixing to fidelity; defer any new feature ideas to a separate plan.
