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
| S-07 Match Analysis (live / in-progress) | `s07-match-analysis.html` | `/match/[id]` | Read / Verify | `cjx-usage` |
| S-08 Match Preview (upcoming, forecast-led) | `s08-match-preview.html` | `/fixture/[id]` | Anticipate / Verify | `cjx-usage` |
| S-09 System Logs (info/error events) | `s09-logs.html` | `/logs` | Verify / Trust | `cjx-usage` |
| S-10 Match Analysis (completed / full-time) | `s10-match-final.html` | `/match/[id]` | Read / Verify | `cjx-usage` |
| S-11 Private Betting Board | `s11-betting-recommendation.html` | `/betting` | Anticipate / Verify | `cjx-usage` |

> Design-review artifact (not a product screen): `s08-forecast-compare.html` — current vs proposed "ghosted placeholder" forecast card, so a fabricated number is never shown as a working result.

App Shell (top nav `Today` / `Standings` / `Fixtures` / `Archive` / `Changelog`, plus `Betting` on S-11, and footer) is shared across screens. S-07/S-08/S-10 are match-scoped detail pages (no top-nav entry): the live (S-07) and completed (S-10) match pages are reached from the brief (S-02) and the home "Up next" / live card (S-01); the upcoming preview (S-08) from the home "Up next" card and fixture rows (S-05).

**Match analysis pages — one file per match state:**
- **S-07 (live / in-progress):** green in-progress banner with live score + match clock, **goalscorers in the hero** (name + minute), a "Watch live on SBS" link, pre-match forecast, key moments so far, live stats, and a live standings projection ("if the score holds").
- **S-10 (completed / full-time):** final-score hero, the verdict, pre-match forecast, a **forecast-vs-result conclusion** (did the model call it — hit/miss), key moments, goalscorers, final stats, and confirmed standings impact. Flow is forecast → conclusion → actual.
- **S-08 (upcoming):** leads with the **forecast as primary content** (win probability + projected verdict), then the factual evidence — team comparison (stat bars), head-to-head, qualification stakes, players to watch, strengths & weaknesses, and "what to watch".
- The **forecast block is deliberately quarantined and badged "model preview · experimental"** across all three: the prediction engine is roadmap-only and the product does not present LLM-invented predictions as fact; percentages, factor weightings, and the verdict are illustrative placeholders. Match statistics (xG, shots, possession) and head-to-head come from the paid API-Football plan used in production.
- The dedicated **"Recent form" section was removed** from the match pages; recent form still appears as one labelled signal inside the forecast factors.

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
| `components.css` | Reusable components (UI_SPEC §2.4): cards, ResultChip, LiveBadge, PositionDelta, QualificationTag, Sparkline, DateStamp, StandingsTable, EmptyState, SkeletonCard, FixtureRow, KnockoutBracket (CSS-only tree), Changelog timeline. Match-analysis: match/live hero (`.match-hero`, `.next-match.is-live`), stat bars, head-to-head, players, forecast card + factors + verdict, forecast-vs-result conclusion (`.fc-outcome`), strengths & weaknesses (`.sw-grid`), goalscorer cards (`.scorer-card`), flag backdrop (`.flag-bg` / `.page-flag-bg`) |
| `interactions.js` | CJX entrance animations + segmented toggle (Standings groups/knockout, Fixtures upcoming/knockout); inline SVG flag injection (`FLAGS` map → `[data-flag]`, plus `[data-flag-bg]` / `[data-flag-bg-page]` backdrops); countdown / live-clock timers |

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
- **Two-team flag backdrop.** Match heroes and the whole page can render a faded home/away flag layer — `data-flag-bg` on a hero container, `data-flag-bg-page` on `<body>`, both reading `data-home` / `data-away` (FIFA codes) — reusing the same `FLAGS` map. Home flag fills the left, away the right, under a dark tint for readability; flag-backed heroes drop the decorative football.
- **Goalscorers & live scorers.** Scorer cards (`.scorer-card`) list each goal with player, minute, and type. The live page (S-07) also shows a compact scorers strip inside the hero (name + minute, grouped by team).
- **Forecast-vs-result conclusion.** On the completed page (S-10), `.fc-outcome` renders a hit/miss comparison of the pre-match forecast against the final result.
- **Private betting board prototype.** S-11 ranks upcoming fixtures by strongest model win lean, separates model fair price from TAB odds, and provides personal choice states: back, watch price, or skip. It is a private decision page, not a public recommendation page.
- The `FLAGS` map and `data-*` values are author-controlled constants in static files (no user input), so the `innerHTML` injection carries no XSS exposure here; sanitize if this ever renders dynamic data.
