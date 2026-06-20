# Phase 8: Frontend Prototype Parity — Closure

**Date**: 2026-06-20 14:30
**Severity**: Low (feature complete, no blockers)
**Component**: Frontend (Next.js 16, React 19, Tailwind v4)
**Status**: Resolved

## What Happened

Phase 8 shipped a complete frontend implementation closing the gap between live site and HTML prototypes. Built two new screens (`/fixtures`, `/changelog`), extended navigation to 5 links, added data-backed visual polish (team flags, countdown clocks, live badges, "Up next" featured card, "Stars to watch" top-scorer strip), and wired all to Phase 7 API (fixtures, knockout bracket, top scorers, team logos).

**Delivered:** 8 new components (team-flag, countdown, live-badge, fixture-row, knockout-bracket, star-card, nav-links, fixtures-view), two new pages, enhanced home, nav with active-route highlighting. Build clean, SSR/hydration verified, responsive, accessible (color never sole signal, countdown aria-hidden, reduced-motion respected). Commit: `15c4bbba` (feat: add fixtures, knockout bracket, changelog, stars + team flags).

## The Brutal Truth

This phase exposed three subtle friction points that shouldn't have surprised but did. The Changelog deployment trap is the kind of thing that bites in production at 2am when someone deploys from main without realizing a file at the root doesn't ship. The hydration divergence was caught in code review but felt like a gotcha we should have anticipated earlier — "always verify SSR/client agreement on formatted dates" is now a mental checklist item. The scope creep wasn't really creep; it was honest — we shipped what we could verify offline, left placeholder states for real data, and honestly marked the brief-card flags as N/A rather than faking data. That honesty cost nothing and saved future confusion.

## Technical Details

1. **Changelog file location mismatch (caught pre-merge)**
   - Plan: `CHANGELOG.md` at repo root
   - Reality: Next.js standalone build ships only `public/` + traced files; root files don't reach the container
   - Dockerfile `COPY public` works, but root `CHANGELOG.md` is unreachable
   - Fix: Moved to `frontend/public/CHANGELOG.md` (single source, safe in dev + prod)
   - Lesson: The build context is smaller than you think. Verify `next build` output includes every user-facing static file.

2. **SSR/client hydration mismatch on date formatting**
   - Issue: fixtures day headers formatted in "use client" component without timezone pin
   - Divergence: SSR runs in server timezone (likely UTC), client in browser timezone → headers shift between SSR and post-hydration
   - Fix: Anchor day headers to UTC calendar date (noon-UTC, `timeZone: "UTC"`) so both server and browser agree
   - Code: `new Date(kickoff_utc).toLocaleDateString('en-AU', { timeZone: 'UTC' })`
   - This should be a pattern: any date/time formatted in a client component without explicit timezone pin will hydrate-mismatch. Document this.

3. **Countdown hydration (client-side logic, no mismatch)**
   - Renders static `"—"` placeholder server-side, mounts to live countdown via `useEffect`
   - Interval self-clears at zero (becomes LIVE) and on unmount
   - `aria-hidden` on the countdown; static AEST time label carries the accessible text for screen readers
   - `prefers-reduced-motion` drops to 60s polling (no per-second animation)
   - Verified: no hydration warnings, Lighthouse a11y 100

4. **Scope decision: brief-card flags marked N/A**
   - Plan listed "flags on brief result chips"
   - Reality: live `brief-card` component has only title/summary; no match-result data (scores/goals)
   - Options: (a) invent fake data, (b) skip it, (c) add data-fetching to brief-card (out of scope), (d) mark N/A
   - Chose (d): honest scope cut in the phase file, no hidden tech debt
   - Impact: zero; prototype has no result chips either. The home page stats show flags on standings only.

5. **Empty states + offline API resilience**
   - All 8 new components tested with backend down or API_FOOTBALL_KEY missing
   - Fixtures: shows empty "No upcoming matches" + empty knockout bracket
   - Standings/brief: render with no logos (team initials + colored fallback crest)
   - External `<img>` + `onerror` fallback (no broken images, matches prototype pattern, no `next.config` remote-host setup)
   - Build: `npm run build` with Docker postgres down → clean; SSR test with backend down → all pages 200 (no 500s)

## What We Tried

- Initial plan had `CHANGELOG.md` at repo root; realized during Docker layer review that root files weren't copied; moved to `public/` without rework.
- Caught hydration divergence in code review (fixtures day headers), fixed with explicit UTC timezone anchor before merge.
- Tested countdown interval cleanup on unmount + reduced-motion; Lighthouse confirms no memory leaks or a11y issues.
- Verified empty states with mock API (all 6 prototype screens render cleanly with no data).

## Root Cause Analysis

1. **Changelog gotcha**: Build context assumption not surfaced early. The plan didn't explicitly say "verify the file lands in the container." Should have traced from source → COPY → deployed artifact.

2. **Hydration mismatch**: Timezone handling in date formatting isn't obvious when the component is client-side but SSR happens server-side. The fix is straightforward (`timeZone: "UTC"`) but only if you know to look. Pattern missing from team knowledge.

3. **Scope honesty**: The brief-card limitation isn't a failure; it's a real constraint (component designed for title/summary only). Marking it N/A instead of inventing data was the right call, but it means the "flags" requirement is partially deferred (they exist on standings, not brief).

## Lessons Learned

1. **Build context is not the repo.** When shipping with Docker, trace every user-facing static file from source → `COPY` instruction → final artifact. Root-level files are easy to miss.

2. **Timezone is a silent killer.** Any date/time formatted in a client component without explicit timezone will diverge on hydration. Document and enforce: `timeZone: "UTC"` or `timeZone: navigator.resolvedOptions().timeZone` (if you want browser local).

3. **Empty states are not second-class.** Real data is delayed (API_FOOTBALL_KEY collection + season 2022). Empty states are the product until then. Invest in them; don't ship broken-looking fallbacks.

4. **Honest scope cuts save cycles.** We could have hacked fake match data into brief-card; instead we marked it N/A. That clarity costs nothing and prevents future "why is this data invented?" questions.

5. **Offline + backend-down verification catches deployment surprises.** Testing with `docker-compose down` before merge revealed zero 500s and confirmed fallback chains work. Do this for every data-fetching page.

## Next Steps

- **Before merge to main:** Ensure ck_docs/UI_SPEC.md is up to date with Tailwind v4 tokens and fixture/changelog component specs (currently in phase file; may want central reference).
- **Real data:** Collect API_FOOTBALL_KEY + seed 2022 season in dev database; then run `/collect-fixtures` + `/collect-stats` endpoints to populate fixtures, top scorers. Countdown will tick for real.
- **Follow-up (out of scope):** brief-card match-result flags, sparkline form trends on standings, knockout match-level detail view (see Changelog roadmap).

**Status:** RESOLVED. Code complete, no blockers, real data collection deferred (external dependency).
