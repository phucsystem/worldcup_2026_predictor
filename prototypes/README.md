# World Cup 2026 Intelligence — UI Prototypes

Production-ready HTML/CSS/JS prototypes implementing `ck_docs/UI_SPEC.md`.
Visual direction: dark sports dashboard (FIFA navy + electric royal blue).

Open any `s0X-*.html` directly in a browser. All assets are local (no CDN).

## Screen Index

| Screen | File | Route | CJX Stage | Body Class |
|--------|------|-------|-----------|------------|
| S-01 Daily Brief List (Today) | `s01-brief-list.html` | `/` | Arrive / Scan | `cjx-discovery` |
| S-02 Daily Brief Detail | `s02-brief-detail.html` | `/brief/[date]` | Read / Verify | `cjx-usage` |
| S-03 Standings | `s03-standings.html` | `/standings` | Verify | `cjx-usage` |
| S-04 Archive | `s04-archive.html` | `/archive` | Return | `cjx-retention` |
| S-05 Fixtures (Upcoming + Knockout) | `s05-upcoming-knockout.html` | `/fixtures` | Verify / Anticipate | `cjx-usage` |
| S-06 Changelog | `s06-changelog.html` | `/changelog` | Trust / Share | `cjx-retention` |

App Shell (top nav `Today` / `Standings` / `Fixtures` / `Archive` / `Changelog` + footer) is shared across all screens.

## FR / Requirement Mapping

> No formal `SRD.md` exists yet. FR references derive from the brainstorm report; reconcile when `/ipa:spec` mints canonical FR-xx (UI_SPEC §6, Open Question 1).

| Screen | Requirement (brainstorm / UI_SPEC §6) |
|--------|----------------------------------------|
| S-01 Brief List | Expected output V1.2 — brief list, latest first |
| S-02 Brief Detail | Expected output V1.1–2 — articles (title/summary/body_md); Acceptance (correct end-to-end brief); provenance via `model_used` |
| S-03 Standings | Expected output V1.2 — standings; DB `standings`; Acceptance (deterministic Python math, LLM narrates only) |
| S-04 Archive | Expected output V1.2 — archive |
| S-05 Fixtures | Brainstorm scope — fixtures + qualification scenarios; DB `matches` (scheduled) + knockout bracket |
| S-06 Changelog | Brainstorm — "lasting asset = portfolio"; P-04 transparency |
| App Shell footer | Scheduling: daily 7:00 AM Australia/Melbourne |

## Shared Files

| File | Purpose |
|------|---------|
| `styles.css` | Design tokens (UI_SPEC §2) + app-layout / top-nav shell + typography |
| `components.css` | Reusable components (UI_SPEC §2.4): cards, ResultChip, LiveBadge, PositionDelta, QualificationTag, Sparkline, DateStamp, StandingsTable, EmptyState, SkeletonCard, FixtureRow, KnockoutBracket (CSS-only tree), Changelog timeline |
| `interactions.js` | CJX entrance animations + segmented toggle (Standings groups/knockout, Fixtures upcoming/knockout) |

## Notes on spec adherence

- **Top nav, not sidebar.** UI_SPEC App Shell specifies a top nav bar ("nav collapses to a single row of text links on mobile"), so the prototype uses a sticky top nav. The `app-layout` / `main-content` / `sidebar` layout classes are retained but applied to a top-nav shell.
- **States included.** Each screen shows its real content plus its empty/error state per UI_SPEC §5 (S-01 no-brief-yet, S-03 knockout locked, S-04 no-archive). A `SkeletonCard` style is provided in `components.css`.
- **Numbers are deterministic-by-design.** Standings tables use tabular-nums, position-delta arrows (▲/▼/–), and qualification icons (●/○/✕) — color is never the sole signal (a11y, UI_SPEC §5).
- **Reduced motion** disables LiveBadge pulse, sparkline, skeleton shimmer, and CJX entrance.
- Reading column = 960px; standings column = 1120px; page body never scrolls horizontally (wide tables scroll inside `.table-container`).

## Enhancements (flags, stars, motion)

- **Team flags** are inline SVG, injected from a single `FLAGS` map in `interactions.js` (one source of truth → DRY). They render identically on every OS — unlike regional-indicator emoji, which fail on Windows. Any team without a built flag falls back to a colored **code crest** (e.g. `KSA`). Flags are simplified geometric renderings (emblems approximated) to stay self-contained with no network dependency.
- **Stars to watch** (S-01) shows player photos pulled from Wikimedia Commons URLs. These are *illustrative external assets* — each `<img>` has an `onerror` fallback to a team-colored initials avatar, so a failed/offline load never shows a broken image. For a real product, replace with licensed assets.
- **Motion:** staggered entrance for cards/rows, sparkline line-draw, and press/hover feedback — all gated by `prefers-reduced-motion` (entrance + draw animations disabled when requested).
- **Countdown clocks** for upcoming matches (`[data-countdown]` in `interactions.js`): a segmented H/M/S clock on the home "Up next" featured card and compact inline `in 3h 57m` counters on fixture rows. Targets derive from `data-offset-min` at load, so the prototype always ticks realistically regardless of when opened; rolls to a **LIVE** badge at zero. For production, swap to an absolute `data-kickoff` ISO timestamp. Marked `aria-hidden` (the static kickoff label carries the accessible time) to avoid per-second screen-reader spam.
- The `FLAGS` map and `data-*` values are author-controlled constants in static files (no user input), so the `innerHTML` injection carries no XSS exposure here; sanitize if this ever renders dynamic data.
