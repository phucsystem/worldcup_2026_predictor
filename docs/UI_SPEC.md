# UI Specification (Basic Design / 外部設計)

**Project:** World Cup 2026 Intelligence
**Stage:** IPA Basic Design (UI_SPEC)
**Date:** 2026-06-19
**Requirement basis:** `ck_plans/reports/brainstorm-design-260619-1018-world-cup-intelligence-report.md` (approved). No `SRD.md` exists yet — FR references below are derived from the brainstorm and should be reconciled when `/ipa:spec` produces a formal SRD.
**Design reference:** FIFA World Cup 2026 official site (`fifa.com`) — palette extracted from supplied screenshot.
**Visual direction:** Sports dashboard — dark, data-dense, card-based.

---

## 1. Customer Journey Experience (CJX)

### 1.1 User Personas

| ID | Persona | Role | Goals | Pain Points |
|----|---------|------|-------|-------------|
| P-01 | **The Morning Reader** | Engaged football fan | One trustworthy daily catch-up brief; no doom-scrolling 5 sites | Scattered scores/news; recency noise; doesn't want live blow-by-blow |
| P-02 | **The Standings Checker** | Competitive-context fan | Exact group points, qualification scenarios, who advances | Tables elsewhere are stale, inconsistent, or buried under ads |
| P-03 | **The Archive Browser** | Catch-up / returning user | Read briefs missed while away; follow a storyline over days | Hard to find "what happened on day X"; no clean back-catalog |
| P-04 | **The Evaluator** | Recruiter / portfolio viewer | Judge product polish + that the pipeline is real and reliable | Demos that look fake; broken states; no proof of automation |

**Primary persona:** P-01 (drives the home + detail experience). P-02 drives Standings. P-03 drives Archive.

### 1.2 Customer Journey Map

| Stage | User action | Touchpoint (screen) | Emotion | Design response |
|-------|-------------|---------------------|---------|-----------------|
| **Arrive** | Opens site in the morning | S-01 Brief List | Curious, time-poor | Today's brief is the hero; date + freshness stamp instantly visible |
| **Scan** | Reads headline + summary deck | S-01 / S-02 | Wants the gist fast | Headline + 2-line summary above the fold; result chips for completed matches |
| **Read** | Reads full brief, checks a table inline | S-02 Brief Detail | Engaged | Markdown body with embedded standings block; tabular numbers |
| **Verify** | Checks a group / qualification | S-03 Standings | Wants certainty | Deterministic Python-computed tables; position-delta arrows; qualified/eliminated state |
| **Return** | Comes back later, reads missed days | S-04 Archive | Catching up | Date-grouped list; one tap to any past brief |
| **Trust** | Notices it updates daily, never breaks | All + empty/error states | Reassured | Honest "next brief at 7:00 AM AEST" affordance; graceful empty/stale states |

---

## 2. Design System

> Extracted from the FIFA WC2026 reference (navy + electric royal blue + white) and adapted to a **dark sports-dashboard** theme. Dark is the default and primary theme; an optional light variant is out of V1 scope.

### 2.1 Color Palette

**Surfaces (dark theme — default)**

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#060E22` | Page background (deep navy-black) |
| `--surface` | `#0A1B3D` | Cards, header bar, table containers (FIFA navy) |
| `--surface-elevated` | `#13294F` | Hover cards, modals, active rows |
| `--border` | `#1E3157` | Hairlines, table dividers, card outlines |

**Brand / Accent (from FIFA hero blues)**

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `--primary` | `#2D6BF6` | rgb(45,107,246) | Links, primary buttons, active nav, key numbers |
| `--primary-hover` | `#1E54E0` | rgb(30,84,224) | Button/link hover, pressed |
| `--accent-bright` | `#4D8BFF` | rgb(77,139,255) | Focus glow, sparkline highlights, badges |
| `--primary-deep` | `#1A3AD0` | rgb(26,58,208) | Gradient base for hero/banner blocks |

**Text**

| Token | Hex | Usage |
|-------|-----|-------|
| `--text-primary` | `#FFFFFF` | Headlines, primary copy, key stats |
| `--text-secondary` | `#A9B6D4` | Summary decks, labels, metadata |
| `--text-muted` | `#6B7A9E` | Timestamps, captions, disabled |

**Status (match / qualification semantics)**

| Token | Hex | Meaning |
|-------|-----|---------|
| `--status-live` / win / qualified | `#2BD37E` | Live indicator, W, advanced/qualified |
| `--status-draw` | `#F4B740` | Draw, "in contention", warning |
| `--status-loss` / eliminated | `#FF5A5A` | L, eliminated, error |
| `--status-neutral` | `#6B7A9E` | Not started, N/A |

**Accessibility:** All text/background pairs target WCAG AA (≥4.5:1 body, ≥3:1 large). `--primary` on `--bg` and white-on-`--surface` both pass. Status colors are always paired with an icon/letter (W/D/L, ▲/▼) — never color alone.

### 2.2 Typography

System-first stack (zero font-CDN dependency; ships fast for the ~30-day window). Display weight carries the "bold sports" feel.

| Element | Family | Size | Weight | Line height | Notes |
|---------|--------|------|--------|-------------|-------|
| Display (brief headline) | Inter / system-ui | 32px / 2rem | 800 | 1.15 | Tight, bold; 40px on ≥lg |
| H1 (page title) | Inter / system-ui | 28px | 700 | 1.2 | |
| H2 (section) | Inter / system-ui | 22px | 700 | 1.25 | |
| H3 (card/group title) | Inter / system-ui | 16px | 600 | 1.3 | Uppercase, letter-spacing 0.04em for group labels |
| Body | Inter / system-ui | 16px | 400 | 1.6 | Brief markdown body |
| Summary deck | Inter / system-ui | 18px | 400 | 1.5 | `--text-secondary` |
| Label / meta | Inter / system-ui | 13px | 500 | 1.4 | Uppercase metadata |
| **Numeric (tables/scores)** | `font-variant-numeric: tabular-nums` | inherit | 600 | — | Critical: columns must align |

`font-family` stack: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.

### 2.3 Spacing, Radius, Elevation

- **Spacing scale (px):** 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 (8px base grid).
- **Radius:** card `12px`, chip/badge `999px` (pill), input `8px`.
- **Elevation:** flat by default (dark theme uses surface tone shifts, not shadows). Modal/hover: `0 8px 24px rgba(3,8,20,0.6)` + `--surface-elevated`.
- **Container:** max-width `960px` (reading column) for briefs; `1120px` for standings.

### 2.4 Core Components (atoms/molecules)

| Component | Type | States | Action |
|-----------|------|--------|--------|
| `Button` (primary) | Action | default, hover, focus-visible, active, disabled | Submit / navigate |
| `NavLink` | Nav | default, hover, active (current route), focus | Route change |
| `ResultChip` | Display | win, draw, loss | Shows `BRA 3–1 SRB`; color-coded letter |
| `LiveBadge` | Status | live (pulse), final, scheduled | Match status |
| `PositionDelta` | Display | up (▲ green), down (▼ red), same (–) | Standings movement vs prev snapshot |
| `QualificationTag` | Status | qualified, in-contention, eliminated | Group-stage outcome |
| `Sparkline` | Data viz | n/a | Team form trend (last N results) |
| `DateStamp` | Meta | fresh (today), past | Brief date + "Updated 7:00 AM AEST" |
| `StandingsTable` | Data | default, row-hover, highlight (user-focused team) | Sortable static table |
| `EmptyState` | System | no-brief-yet, stale, error | "Next brief at 7:00 AM AEST (Australia/Melbourne)" |
| `SkeletonCard` | System | loading | SSR fallback / streaming |
| `Flag` | Display | rendered, fallback-crest | Inline SVG team flag (OS-consistent); code-crest fallback for uncovered teams |
| `Crest` | Display | default, sm | Team-color circle with 3-letter code (ESPN-style); flag fallback + player team tag |
| `StarCard` | Display | photo, initials-fallback | Player headshot with `onerror` → team-colored initials avatar |

**Motion:** staggered list/grid entrance (rise-in), sparkline line-draw, and press/hover scale feedback — all disabled under `prefers-reduced-motion` (§5). Player photos are illustrative external assets with a guaranteed initials fallback; flags are self-contained inline SVG.

---

## 3. Screen Specifications

> 4 V1 screens + a shared App Shell. Maps to brainstorm "Expected output (V1)": brief list + brief detail + standings tables + archive. Match/fixture detail and live scores are explicitly out of V1 scope.

### App Shell (global)

**Components:** top nav bar (`--surface`), brand mark "WC26 Intelligence", nav links `Today` / `Standings` / `Fixtures` / `Archive` / `Changelog`, current-route active state. Footer: data-source attribution + "Auto-published daily, 7:00 AM Australia/Melbourne". Responsive: nav stays a single row of text links on mobile; if the links exceed width they scroll horizontally inside the bar (no hamburger).

---

### S-01: Daily Brief List (Home / "Today")

**Refs:** brainstorm §"Expected output (V1).2" (brief list), FR-derived: *list of daily briefs, latest first*. CJX Stage: Arrive / Scan.
**User goal (P-01):** Get today's morning brief instantly, scan recent days.
**Route:** `/`

**Layout (desktop):**
```
┌──────────────────────────────────────────────┐
│  WC26 Intelligence      Today  Standings  Archive │  ← App Shell
├──────────────────────────────────────────────┤
│  TODAY · 19 JUN 2026 · Updated 7:00 AM AEST    │  ← DateStamp (fresh)
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│  ┃  Brazil seize Group G as Serbia stumble ┃ │  ← hero brief card
│  ┃  Summary deck — two lines, secondary.    ┃ │
│  ┃  [BRA 3–1 SRB] [ARG 2–0 ...] result chips┃ │
│  ┃  Read brief →                            ┃ │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│  EARLIER                                       │
│  ┌──────────────┐ ┌──────────────┐            │
│  │ 18 Jun · card │ │ 17 Jun · card│  ...       │  ← compact brief cards (grid)
│  └──────────────┘ └──────────────┘            │
└──────────────────────────────────────────────┘
```

**Components:**
| Component | Type | States | Action |
|-----------|------|--------|--------|
| Hero brief card | Card | default, hover (elevate), focus | → S-02 (today's brief) |
| Compact brief card | Card | default, hover, focus | → S-02 (that date) |
| Result chips (in card) | ResultChip | win/draw/loss | Non-interactive summary |
| DateStamp | Meta | fresh | — |
| Today's results | ScoreCard grid | final (FT) | Completed matches today: flags + score + group; winner emphasized |
| Up next | NextMatch + fixture rows | scheduled | Featured next kickoff (accent card) + 2 compact fixtures → "See all fixtures" (S-05) |
| EmptyState | System | no-brief-yet | Shown pre-7AM / first run: "Today's brief publishes at 7:00 AM AEST" |

**Behavior:** SSR-rendered, newest brief = hero. Below the hero: **Today's results** (completed `matches` with status=FT, scores from data — never LLM) and **Up next** (soonest scheduled fixtures, featured card highlights the next kickoff, links to S-05). Then latest 7–10 brief cards → "View archive →" (S-04). Mobile: single-column stack, score grid reflows to one column.

**Design rationale (CJX):** P-01 is time-poor → today's headline + deck + result chips must be readable without a click; the "Read brief →" affordance is the only required CTA.

---

### S-02: Daily Brief Detail

**Refs:** brainstorm §"Expected output (V1).1–2" (articles: title, summary, markdown body), §Acceptance ("one correct end-to-end brief"). CJX Stage: Read / Verify.
**User goal (P-01):** Read the full daily intelligence brief; glance at the relevant standings inline.
**Route:** `/brief/[date]` (e.g. `/brief/2026-06-19`)

**Layout:**
```
┌──────────────────────────────────────────────┐
│  ‹ Back to Today          19 JUN 2026 · AEST   │
│  Brazil seize Group G as Serbia stumble        │  ← Display headline (32–40px)
│  Summary deck paragraph, 18px secondary.       │
│  ────────────────────────────────────────────  │
│  Markdown body (prose, 16px / 1.6, 960px col): │
│    ## Group G                                   │
│    Narrative paragraphs …                        │
│    ┌── embedded StandingsTable (Group G) ──┐    │
│    │ Team   P  W  D  L  GF GA GD Pts  ±     │    │
│    │ Brazil 3  3  0  0  7  1  +6  9  ▲1     │    │
│    └─────────────────────────────────────┘    │
│    ## Upcoming                                  │
│  ────────────────────────────────────────────  │
│  model: deepseek · generated 07:00 AEST         │  ← provenance footer
└──────────────────────────────────────────────┘
```

**Components:**
| Component | Type | States | Action |
|-----------|------|--------|--------|
| Back link | NavLink | default, hover, focus | → S-01 |
| Display headline | Text | — | — |
| Summary deck | Text | — | — |
| Markdown body | Prose | — | Renders agent `body_md`; sanitized |
| Embedded StandingsTable | Data | row-hover, qualification tags | Inline group table(s) referenced by the brief |
| PositionDelta | Display | up/down/same | In embedded table |
| Provenance footer | Meta | — | `model_used`, generated timestamp (transparency for P-04) |

**Behavior:** SSR; markdown rendered server-side and sanitized (no raw HTML injection from LLM output). Standings blocks come from deterministic `standings` data, **not** from LLM-generated numbers (correctness control). Unknown/old date → 404 with link back to Archive.

**Design rationale:** Provenance footer + Python-computed tables directly serve P-04's "is this real and reliable?" and the brainstorm's top correctness control (zero table-math hallucination).

---

### S-03: Standings

**Refs:** brainstorm §"Expected output (V1).2" (standings tables), §DB `standings`, §Acceptance (deterministic computation). CJX Stage: Verify.
**User goal (P-02):** Read exact, current group standings and qualification state.
**Route:** `/standings`

**Layout:**
```
┌──────────────────────────────────────────────┐
│  Standings            Snapshot: 19 Jun 2026     │
│  [ Groups ]  [ Knockout ]   ← segmented toggle  │
│  GROUP A                                        │
│  ┌────────────────────────────────────────┐   │
│  │ #  Team        P  W D L  GF GA GD Pts ± │   │
│  │ 1  ● Mexico    3  2 1 0   5  2 +3   7 ▲1 │   │  ← qualified (green dot)
│  │ 2  ● Norway    3  2 0 1   4  3 +1   6 –  │   │
│  │ 3  ○ Croatia   3  1 0 2   2  4 -2   3 ▼1 │   │  ← in contention
│  │ 4  ✕ ...       3  0 1 2   1  6 -5   1    │   │  ← eliminated
│  └────────────────────────────────────────┘   │
│  GROUP B … (repeat for all groups)              │
└──────────────────────────────────────────────┘
```

**Components:**
| Component | Type | States | Action |
|-----------|------|--------|--------|
| Snapshot date | Meta | — | Which `snapshot_date` is shown |
| View toggle | Segmented control | groups (default), knockout | Switch group tables ↔ bracket |
| StandingsTable (per group) | Data | row-hover, highlight | Static, pre-sorted by position |
| QualificationTag | Status | qualified ●, contention ○, eliminated ✕ | Visual + icon, never color-only |
| PositionDelta | Display | ▲ up / ▼ down / – same | vs `prev_position` |
| KnockoutBracket | Data viz | locked (group stage), populated | Read-only bracket once knockouts begin |

**Behavior:** SSR, fully Python-computed (P/W/D/L/GF/GA/GD/pts/position/delta from `standings` snapshot). Knockout tab is empty-stated until bracket data exists. Mobile: tables scroll horizontally inside an `overflow-x:auto` wrapper; group label sticky.

**Design rationale:** Numbers are the product's credibility. Tabular-nums + delta arrows + explicit qualification icons make the table self-explanatory and trustworthy (P-02, P-04).

---

### S-04: Archive

**Refs:** brainstorm §"Expected output (V1).2" (archive). CJX Stage: Return.
**User goal (P-03):** Find and read any past daily brief.
**Route:** `/archive`

**Layout:**
```
┌──────────────────────────────────────────────┐
│  Archive                  47 briefs            │
│  JUNE 2026                                      │
│   19  Brazil seize Group G as Serbia stumble → │
│   18  Argentina cruise; host nations hold    → │
│   17  Opening upsets reshape Group D         → │
│  ──────────────────────────────────────────    │
│  (year/month grouping as range grows)           │
└──────────────────────────────────────────────┘
```

**Components:**
| Component | Type | States | Action |
|-----------|------|--------|--------|
| Month group header | Meta | — | Groups rows by month |
| Archive row | List item | default, hover, focus | → S-02 (that date) |
| Brief count | Meta | — | Total published briefs |
| EmptyState | System | no-archive | Pre-first-publish: "No past briefs yet" |

**Behavior:** SSR; reverse-chronological, grouped by month. Each row = date + headline + chevron. Given the short tournament window the list stays small (no pagination needed in V1 — note if it grows).

**Design rationale:** P-03 catching up needs the fewest possible taps from "I missed days" → "reading that brief". Date-led rows make scanning by day trivial.

---

### S-05: Fixtures (Upcoming Matches & Knockout Bracket)

**Refs:** brainstorm §"completed matches, **fixtures**, standings, **qualification scenarios**" + DB `matches` (status=scheduled) and knockout bracket. CJX Stage: Verify / Anticipate.
**User goal (P-02):** See what's coming next and how the knockout tree is shaping up.
**Route:** `/fixtures`

**Layout:**
```
┌──────────────────────────────────────────────┐
│  Fixtures            Times in AEST (Melbourne) │
│  [ Upcoming ] [ Knockout ]  ← segmented toggle │
│  TODAY · 19 JUN 2026                            │
│  ┌──────────────────────────────────────────┐ │
│  │ 05:00  🇧🇷 Brazil  vs  🇷🇸 Serbia  [Group G]│ │  ← fixture rows
│  │        SoFi Stadium, Inglewood            │ │
│  └──────────────────────────────────────────┘ │
│  FRI · 20 JUN 2026 … (day-grouped)             │
│                                                 │
│  — Knockout view —                              │
│  R16        QF        SF      Final             │
│  ┌────┐                                         │
│  │1A  │──┐                                       │
│  └────┘  ├──┌────┐                              │
│  ┌────┐──┘  │ QF1│──┐   …  bracket tree         │
│  │2B  │     └────┘  ├── SF1 ── Final ── 🏆       │
│  └────┘             …                           │
└──────────────────────────────────────────────┘
```

**Components:**
| Component | Type | States | Action |
|-----------|------|--------|--------|
| View toggle | Segmented control | upcoming (default), knockout | Switch fixture list ↔ bracket |
| Fixture row | List item | scheduled | Kickoff time (AEST) + teams + group pill + venue |
| Day group header | Meta | today, future | Groups fixtures by calendar day |
| KnockoutBracket | Data viz | projected (seeds), decided (team confirmed), TBD | Read-only R16→Final tree + connectors |
| Bracket card | Card | decided (highlight), pending | One matchup; shows seed label or confirmed team |
| Champion card | Display | TBD, decided | Final winner callout |
| Third-place row | List item | scheduled | 3rd-place playoff fixture |

**Behavior:** SSR. Upcoming = scheduled `matches` ordered by kickoff, grouped by day, times converted to Australia/Melbourne. Knockout = projected bracket; slots show group seeds (`1A`, `2B`) until a group is decided, then the confirmed team + flag. **Hovering any match traces its winner's path to the final** (downstream cards + connectors light in accent blue, others dim); the champion slot gets a gold trophy treatment. No fabricated scores (consistent with the deterministic-data correctness control). Bracket is horizontally scrollable inside its own container on narrow viewports; page body never scrolls horizontally.

**Design rationale:** Serves P-02's "who advances / what's next" question and the brainstorm's "qualification scenarios" without any LLM-invented results — the bracket is structure + seeds, not predictions.

---

### S-06: Changelog (Project Progress)

**Refs:** brainstorm §"Lasting asset = reusable pipeline + portfolio"; transparency for P-04 (Evaluator). A sharing-oriented public progress log.
**User goal (P-04):** See the platform is real, actively shipping, and reliable; have something shareable to point others to.
**Route:** `/changelog`

**Layout:**
```
┌──────────────────────────────────────────────┐
│  Changelog                                      │
│  What's shipping. Newest first.                 │
│  ● v0.4.0 · 19 Jun 2026  [Latest]               │  ← timeline node + version
│  │  [Added]    Fixtures page + knockout bracket │
│  │  [Improved] Mobile nav scrolling             │
│  ● v0.3.0 · 18 Jun 2026                          │
│  │  [Added]    Next.js SSR site (4 screens)     │
│  ● v0.1.0 · 16 Jun 2026                          │
│  │  [Milestone] First end-to-end brief in DB    │
│  ── On the roadmap ──                            │
│  ☐ Premium model path · ☐ Prediction agent      │
└──────────────────────────────────────────────┘
```

**Components:**
| Component | Type | States | Action |
|-----------|------|--------|--------|
| Changelog timeline | List | — | Vertical rail with a node per release |
| Changelog entry | Card | latest (green node), prior | Version + date + change list |
| Change tag | Badge | added, improved, fixed, milestone | Color + label (never color-only) |
| Roadmap card | Card | upcoming (unchecked) | Not-yet-shipped items |

**Behavior:** Static content for V1 (hand-authored entries reflecting plan phases). Newest entry top, flagged "Latest". Reading column (960px). Change tags map to status colors (Added=green, Improved=blue, Fixed=amber, Milestone=blue) and always carry a text label.

**Design rationale:** Directly serves the brainstorm's portfolio/showcase goal and P-04's trust journey — a shareable, honest record of progress separate from the football content.

---

## 4. Responsive Behavior

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | <640px | Single column; nav as inline text row; tables horizontal-scroll wrapper; hero card full-width |
| Tablet | 640–1024px | Brief grid 2-col; standings full tables |
| Desktop | ≥1024px | Reading column 960px; standings 1120px; brief grid 2–3 col |

Non-negotiables: page body never scrolls horizontally; wide tables scroll inside their own container; `max-width:100%` media.

---

## 5. Accessibility & States Checklist

- Keyboard: all nav/cards/rows focusable, visible `focus-visible` ring (`--accent-bright`, 2px).
- Status never color-only (W/D/L letters, ▲/▼ arrows, ●/○/✕ qualification icons).
- Every screen specifies **loading** (skeleton/SSR), **empty** (pre-publish), and **error/404** states.
- `prefers-reduced-motion`: LiveBadge pulse + sparkline animation disabled.
- Semantic tables (`<table>`, `<th scope>`), landmark regions, single `<h1>` per page.

---

## 6. Traceability (UI → requirements)

| Screen | Brainstorm requirement |
|--------|------------------------|
| S-01 Brief List | Expected output V1.2 (brief list) |
| S-02 Brief Detail | Expected output V1.1–2 (articles: title/summary/body_md); Acceptance (correct end-to-end brief); provenance via `model_used` |
| S-03 Standings | Expected output V1.2 (standings); DB `standings`; Acceptance (deterministic Python math, LLM narrates only) |
| S-04 Archive | Expected output V1.2 (archive) |
| S-05 Fixtures | Brainstorm scope (fixtures, qualification scenarios); DB `matches` (scheduled) + knockout bracket |
| S-06 Changelog | Brainstorm "lasting asset = portfolio"; P-04 transparency |
| App Shell footer | Scheduling: daily 7:00 AM Australia/Melbourne |

---

## Open Questions

1. **No formal `SRD.md`** — FR IDs above are derived from the brainstorm. Run `/ipa:spec` to mint canonical FR-xx and reconcile this UI_SPEC's references.
2. **Brief↔Standings linkage** — does each daily brief reference a specific `snapshot_date` of standings to embed (S-02), or always "latest"? Affects S-02 data binding.
3. **Knockout bracket** — in V1 scope as a visual, or list-only until knockouts begin (~late June/July)? Brainstorm lists bracket in data scope but not explicitly in V1 UI output.
4. **Light theme** — dark-only for V1 assumed. Confirm no light variant needed.
5. **Path convention** — written to `docs/` (CK workspace) though `.ipa-ck.json` declares `docs/`. Confirm canonical docs dir so downstream `/ipa:*` and `/plan` resolve consistently.
