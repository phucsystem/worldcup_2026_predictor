# Brainstorm — Match Analysis Page (S07 / S08 / S10)

- **Date:** 2026-06-21
- **Prototypes:** `prototypes/s08-match-preview.html` (upcoming), `prototypes/s07-match-analysis.html` (live), `prototypes/s10-match-final.html` (finished)
- **Status:** Design approved, ready for `/ck:plan`
- **Modes:** none (no --html / --wiki)

## Problem statement

Implement a single match-analysis page covering three states (upcoming, live, finished). The prototypes are rich design explorations, but a scout confirmed **~60% of their sections have no backing data** today. The real task is a scope decision, not a straight port: build what is genuinely data-backed and avoid presenting fabricated stats/predictions as fact.

## Requirements (locked)

- **Expected output:** A dynamic route `/match/[fixture_id]` that renders preview / live / finished layouts from real fixture data, plus a new backend single-fixture endpoint and event persistence.
- **Acceptance criteria:**
  1. `/match/[fixture_id]` renders the correct layout for an upcoming, a live, and a finished fixture; 404 on unknown id.
  2. Live page updates score/clock/timeline on a 30s poll without full reload (reuses existing `/api/live` polling pattern).
  3. Every section shows only real data; the forecast card is the **sole** placeholder, unmistakably badged experimental/illustrative.
  4. No fabricated stats / head-to-head / squad content anywhere.
  5. Match cards on existing pages (brief, fixtures, standings) link to the page.
- **Scope boundary (OUT of v1):** match stat-bars (possession/shots/SoT/xG/corners), team-comparison averages, head-to-head, players-to-watch, strengths & weaknesses, all per-match prose (live read / verdict / what-to-watch / conclusion narrative).
- **Non-negotiable constraints:** Next.js 16 App Router + React 19 + Tailwind v4; server components fetch via `lib/api.ts`; no fake data; product principle = never present model-invented predictions as fact.
- **Touchpoints:** `frontend/app/match/[fixture_id]/`, `frontend/components/*`, `frontend/lib/api.ts`, `backend/app/api/fixtures.py`, `backend/app/data/models.py`, the fixture sync job (for events), and link wiring on brief/fixtures/standings pages.

## Codebase context (scout findings)

- **Implemented prototypes:** s01–06, s09. **s07/s08/s10 not implemented; no `/match/[id]` route.**
- **Reusable components:** `LiveMatchCard`, `NextMatchCard`, `TeamFlag`, `StandingsTable`, `StakeCard`, `Sparkline`, `ResultChips`, `QualificationBadge`, `LocalTime`, `DateStamp`. Design tokens already in `globals.css`.
- **Backend:** FastAPI + Postgres. `matches` has `fixture_id, home_team, away_team, home_score, away_score, status, elapsed, kickoff_utc, stage, group_name, events_json (JSONB, currently always null)`. Endpoints: `/api/fixtures/upcoming`, `/api/fixtures/live`, `/api/fixtures/knockout`, `/api/standings`, `/api/stars`. **No single-fixture-by-id endpoint.**
- **Available data:** scores, status/elapsed, kickoff, stage, group; standings (points/position/qualification + last-5 `recent_results`); team logos; events via `APIFootballClient.get_events()` (not persisted).
- **Absent data:** win-probability/forecast (no model — roadmap only), match stats (possession/shots/xG/corners), head-to-head, squads, goalscorer detail (role/#/photo).
- **Fetch pattern:** async server components → `apiFetch<T>` wrapper (`cache: "no-store"`); live polling component-side every 30s.

## Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Data fidelity | **Data-backed MVP only** — build real-data sections, omit unbacked ones |
| 2 | Forecast block | **Port as labelled placeholder** (static illustrative values, "Model preview · experimental") |
| 3 | Per-match prose | **Omit narrative for v1** |
| 4 | Routing | **One adaptive route** `/match/[fixture_id]`, branch by `status` |
| 5 | Finished conclusion | **Slim data-backed** — comparison cells + auto hit/miss badge, no prose, under experimental label |
| 6 | Match stats | **Out of v1** (no data pipeline) |
| 7 | Events source | **Store in sync job**, serve `events_json` from DB |

## Recommended solution

### Route & state model
`frontend/app/match/[fixture_id]/page.tsx` (server component) fetches one fixture, branches on `status`:

| State | `status` | Lineage |
|---|---|---|
| Preview | `NS` | S08 |
| Live | `1H, HT, 2H, ET, BT, P, LIVE` | S07 |
| Finished | `FT, AET, PEN` | S10 |

Live wraps dynamic parts in a client component polling `/api/live` every 30s; preview/finished render static server-side.

### Backend
- New `GET /api/fixtures/{fixture_id}` → `FixtureDetail` = existing `FixtureRow` fields **+ `events: list[Event]`** (goals/cards/subs).
- Populate `events_json` during the existing fixture sync job; serve events from DB.

### Frontend
- **Reuse:** `NextMatchCard` (preview hero), `LiveMatchCard` (live hero), `TeamFlag`, `StakeCard`, `ResultChips`/`Sparkline` (form), `LocalTime`.
- **New components:** `MatchHeroFinal` (`.is-final` banner), `MatchTimeline` (`mt-list` from events), `Goalscorers` (basic: flag/name/minute/type), `FormCompare` (two-team last-5 pips), `QualificationStakes` (group slice + live/confirmed projection), `ForecastCard` (static, badged experimental), `ForecastOutcome` (comparison cells + auto hit/miss badge — finished only).

### Section composition per state
- **Preview (S08):** countdown hero → forecast (placeholder) → recent form → qualification stakes.
- **Live (S07):** live hero (score/clock/banner scorers) → forecast (placeholder, pre-match) → key moments timeline → goalscorers → recent form → live standings projection.
- **Finished (S10):** final hero → forecast (placeholder) → forecast-vs-result (slim) → key moments → goalscorers → confirmed standings impact.

## Risks

- **Thin pages.** After cutting unbacked sections, preview ≈ 4 blocks, live ≈ 6. Honest cost of no-fake-data; accepted.
- **Events persistence** is the one real backend dependency — touches the sync job. Needs care to avoid disrupting existing ingestion. On-demand fetch was the rejected fallback.
- **Link wiring** across brief/fixtures/standings is small but easy to miss.
- **Goalscorer cards** are intentionally minimal (no role/#/notes) — visually lighter than the mockups.

## Success metrics / validation

- All five acceptance criteria above pass.
- Manual check against one upcoming, one live, one finished fixture.
- Confirm no section renders fabricated numbers except the explicitly-badged forecast card.

## Next steps

1. `/ck:plan` this report (suggest TDD mode — touches backend sync + new endpoint with existing test conventions).
2. Phase order: data (events persistence + endpoint) → core (forecast/stakes logic, hit/miss computation) → ui (components + route + link wiring).
