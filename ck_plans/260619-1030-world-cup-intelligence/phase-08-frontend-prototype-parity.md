---
phase: 8
title: "Frontend Prototype Parity"
status: pending
priority: P2
effort: "2-3d"
dependencies: [7]
---

# Phase 8: Frontend Prototype Parity

## Overview
Close the gap between the live Next.js site and `prototypes/`: build the two unbuilt screens (Fixtures, Changelog), extend the nav to 5 links, and add the data-backed visual polish (team flags/logos, countdown clocks, live badges, "Up next", real top-scorer "Stars to watch"). Consumes the Phase 7 API.

## Key Insights
- Stack: Next.js 16 (App Router, async params), React 19, Tailwind v4 (`@theme` in `globals.css`, no config file). Pages are `force-dynamic` / `no-store`.
- Design system + component specs are in `ck_docs/UI_SPEC.md`; reference markup/CSS in `prototypes/` (`components.css`, `interactions.js`, `s05-*.html`, `s06-*.html`). Implement in Tailwind v4 — do not import prototype CSS.
- External images (logos, player photos) via plain `<img>` + `onerror` fallback (matches prototype, no `next.config` remote-host setup, resilient offline).
- Changelog is static repo content rendered as markdown — reuse the brief-detail `react-markdown` + `rehype-sanitize` pattern.

## Requirements
- Functional: `/fixtures` (upcoming + knockout) and `/changelog` render; nav exposes Today / Standings / Fixtures / Archive / Changelog; home shows "Up next" + "Stars to watch"; flags/logos appear on standings, results, fixtures.
- Non-functional: SSR, responsive (mobile single-col, body never scrolls horizontally), a11y (status never color-only; countdowns `aria-hidden` with static time label; semantic tables; single `<h1>`); `prefers-reduced-motion` disables countdown/entrance motion.

## Architecture
### Routing / shell
- `frontend/app/layout.tsx`: nav → 5 links with active-route state; mobile = horizontal-scroll text row.
- `frontend/lib/api.ts`: typed helpers `getUpcomingFixtures()`, `getKnockout()`, `getStars()`; extend standings/result types with optional `logo`.

### New pages
- `frontend/app/fixtures/page.tsx`: segmented toggle (Upcoming | Knockout). Upcoming = day-grouped `FixtureRow`s with kickoff + countdown + flags + live badge. Knockout = `KnockoutBracket` (CSS tree, R16→Final), empty-stated until data exists.
- `frontend/app/changelog/page.tsx`: read repo `CHANGELOG.md`, render sanitized markdown + roadmap section.

### Home enhancements (`frontend/app/page.tsx`)
- "Up next" featured card (soonest fixture + `Countdown`).
- "Stars to watch" strip (top scorers w/ `StarCard`: photo + fallback, goals, team).
- Flags on result chips.

### Shared components (`frontend/components/`)
- `team-flag.tsx` (logo `<img>` + initials/colored-crest fallback on error), `countdown.tsx` (client, ticks from `kickoff_utc`, rolls to LIVE, `aria-hidden`, reduced-motion aware), `live-badge.tsx`, `fixture-row.tsx`, `knockout-bracket.tsx`, `star-card.tsx`.
- Apply `team-flag` in `standings-table.tsx` + `brief-card.tsx` result chips.

### Changelog source
- Create `CHANGELOG.md` at repo root seeded from `prototypes/s06-changelog.html` (v0.1.0→v0.4.0 + roadmap). `/changelog` reads + renders it. New releases = edit the md.

## Related Code Files
- Create: `frontend/app/fixtures/page.tsx`, `frontend/app/changelog/page.tsx`, `frontend/components/{team-flag,countdown,live-badge,fixture-row,knockout-bracket,star-card}.tsx`, `CHANGELOG.md`
- Modify: `frontend/app/layout.tsx` (nav), `frontend/app/page.tsx` (up-next + stars), `frontend/lib/api.ts` (new fetchers + logo type), `frontend/components/standings-table.tsx` + `brief-card.tsx` (flags), `frontend/app/globals.css` (any new tokens/component classes)

## Implementation Steps
1. `lib/api.ts`: add fixtures/knockout/stars fetchers + logo types.
2. Shared components: `team-flag`, `countdown`, `live-badge`, `fixture-row`, `knockout-bracket`, `star-card`.
3. `layout.tsx`: 5-link nav + active state + mobile scroll.
4. `/fixtures` page (toggle + upcoming + knockout).
5. `CHANGELOG.md` + `/changelog` page (sanitized markdown).
6. Home: "Up next" + "Stars to watch"; flags on result chips.
7. Apply flags to standings + brief; a11y + reduced-motion pass.

## Todo List
- [ ] 5-link nav with active state, mobile-friendly
- [ ] `/fixtures` upcoming (day-grouped, countdown, flags) + knockout bracket + empty states
- [ ] `/changelog` renders CHANGELOG.md (sanitized)
- [ ] Home "Up next" + "Stars to watch" (real photos w/ fallback)
- [ ] Flags/logos on standings + result chips
- [ ] `npm run build` clean with backend down; `tsc --noEmit` clean

## Success Criteria
- [ ] All 6 prototype screens have a live route; nav matches prototype.
- [ ] Fixtures shows real upcoming + knockout (2022 demo data); countdowns tick; LIVE at zero.
- [ ] Stars to watch shows real top scorers with photos (fallback on load error).
- [ ] Changelog renders from `CHANGELOG.md`.
- [ ] Responsive + a11y (color never sole signal; reduced-motion respected); body never scrolls horizontally.

## Risk Assessment
- External images may 404/offline → `onerror` fallback mandatory (no broken images).
- Knockout/upcoming empty for 2026 free-plan data → empty states required (prototype already specifies them).
- Tailwind v4 / Next 16 specifics (async params, `@theme`) — follow existing Phase 4/6 patterns; read `node_modules/next/dist/docs/` if unsure.

## Security Considerations
- Sanitize changelog markdown (`rehype-sanitize`); no raw HTML injection.
- Logos/photos rendered via `<img src>` only (no `innerHTML`); URLs are API data, not user input.

## Next Steps
Optional follow-ups (out of scope): sparkline form trends, match-level fixture detail, prediction/odds agent (see Changelog roadmap).
