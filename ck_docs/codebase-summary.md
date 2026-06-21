# Codebase Summary

**Project:** World Cup 2026 Intelligence  
**Last Updated:** 2026-06-21  
**Language Distribution:** Python (backend ~5.2k LOC), TypeScript/React (frontend ~5.2k LOC), Shell/Docker (infra)

---

## 1. Repository Structure

```
worldcup_2026_predictor/
├── backend/                          # FastAPI + pipeline (Python >=3.12)
│   ├── app/
│   │   ├── main.py                   # FastAPI app, routers, CORS, exception handling
│   │   ├── config.py                 # pydantic-settings (env, secrets)
│   │   ├── logging_config.py         # Non-blocking QueueHandler + DB persistence
│   │   │
│   │   ├── api/                      # Route handlers
│   │   │   ├── briefs.py             # GET /api/briefs, /latest, /{date}
│   │   │   ├── standings.py          # GET /api/standings, /trend
│   │   │   ├── fixtures.py           # GET /api/fixtures/*, /api/stars
│   │   │   ├── tournament.py         # GET /api/tournament/summary
│   │   │   ├── logs.py               # GET /api/logs (filter, pagination)
│   │   │   └── admin.py              # POST /api/admin/* (LOCAL ONLY)
│   │   │
│   │   ├── pipeline/                 # LangGraph intelligence pipeline
│   │   │   ├── graph.py              # StateGraph: Collector → Analyst → Editor
│   │   │   ├── state.py              # BriefState TypedDict
│   │   │   ├── nodes_collector.py    # Deterministic Python node (fixtures, standings)
│   │   │   ├── nodes_analyst.py      # DeepSeek json_mode (storylines, ranking)
│   │   │   ├── nodes_editor.py       # DeepSeek json_mode (article title, body)
│   │   │   ├── prompts.py            # LLM prompts (enforce fact-checking)
│   │   │   ├── run.py                # CLI entry: python -m app.pipeline.run --date
│   │   │   ├── scheduler_entry.py    # APScheduler (7:00 AM AEST, DST guard)
│   │   │   └── live_poller.py        # Background process (live scores, 2min polling)
│   │   │
│   │   └── data/                     # Data collection + persistence
│   │       ├── api_football.py       # APIFootballClient + pure parsers
│   │       ├── collect.py            # CLI: fetch → assign groups → compute → upsert
│   │       ├── standings_math.py     # Pure functions (group tables, qualification)
│   │       ├── repository.py         # SQLAlchemy Core upserts
│   │       ├── models.py             # Pydantic models (Match, Standing, Team, etc.)
│   │       └── deepseek.py           # ChatOpenAI wrapper, cost/token tracking
│   │
│   ├── db/
│   │   └── alembic.ini               # Alembic config
│   │   └── versions/                 # Migrations (0001–0006)
│   │
│   ├── tests/                        # Pytest suite
│   │   ├── test_standings_math.py    # Unit tests: group tables, qualification
│   │   ├── test_api_football.py      # Unit tests: API parsing, aggregate quirk
│   │   ├── test_scheduler.py         # DST/timezone tests
│   │   ├── test_fixtures.py          # Fixture shaping tests
│   │   ├── test_live_poller.py       # Live polling logic
│   │   └── conftest.py               # Pytest fixtures
│   │
│   ├── pyproject.toml                # uv, dependencies, pytest config
│   ├── uv.lock                       # Lock file
│   └── .env.example                  # Template (API keys, timezone)
│
├── frontend/                         # Next.js 16 + React 19 (TypeScript)
│   ├── app/
│   │   ├── layout.tsx                # Root layout, fonts, globals.css, gtag
│   │   ├── page.tsx                  # Home: brief + standings + fixtures
│   │   ├── brief/[date]/page.tsx     # Brief detail with markdown
│   │   ├── standings/page.tsx        # Group standings + trend
│   │   ├── fixtures/page.tsx         # Upcoming, live, knockout matches
│   │   ├── archive/page.tsx          # Past briefs (date-grouped)
│   │   ├── changelog/page.tsx        # Changelog (parses public/CHANGELOG.md)
│   │   ├── logs/page.tsx             # App logs UI (search, filter, pagination)
│   │   │
│   │   └── api/                      # Next.js route handlers (same-origin proxies)
│   │       ├── live/route.ts         # GET /api/live → /api/fixtures/live
│   │       └── logs/route.ts         # GET /api/logs → /api/logs (filtered)
│   │
│   ├── components/                   # React components (~28 total)
│   │   ├── match-cards/
│   │   │   ├── live-match-card.tsx   # In-play match (live score polling)
│   │   │   └── next-match-card.tsx   # Upcoming match preview
│   │   ├── standings/
│   │   │   ├── standings-table.tsx   # Group table (position, points, GD, GF)
│   │   │   ├── results-widget.tsx    # Recent results (results.ts deduped)
│   │   │   ├── sparkline.tsx         # SVG trend chart
│   │   │   └── result-chip.tsx       # Single match result (W/D/L badge)
│   │   ├── fixtures/
│   │   │   ├── fixtures-view.tsx     # Upcoming/live/knockout tabs
│   │   │   ├── fixture-row.tsx       # Row item
│   │   │   └── knockout-bracket.tsx  # Bracket layout (stubbed)
│   │   ├── stakes/
│   │   │   ├── stake-grid.tsx        # Qualification stakes (groups)
│   │   │   ├── stake-card.tsx        # Group card
│   │   │   └── qualification-badge.tsx # Status badge
│   │   ├── brief/
│   │   │   ├── brief-card.tsx        # List item with summary
│   │   │   └── brief-detail.tsx      # Full markdown + tables
│   │   ├── stars/
│   │   │   └── star-card.tsx         # Top scorer card
│   │   ├── logs/
│   │   │   └── logs-view.tsx         # Searchable log table (client island)
│   │   ├── data-display/
│   │   │   ├── summary-panel.tsx     # Key metrics header
│   │   │   ├── empty-state.tsx       # No data fallback
│   │   │   └── skeleton-card.tsx     # Loading placeholder
│   │   └── primitives/
│   │       ├── team-flag.tsx         # Flag image + initials fallback
│   │       ├── local-time.tsx        # Australia/Melbourne time, hydration-safe
│   │       ├── countdown.tsx         # Time until match, suppressHydrationWarning
│   │       ├── position-delta.tsx    # ↑/↓ arrow
│   │       ├── live-badge.tsx        # "LIVE" indicator
│   │       ├── date-stamp.tsx        # Formatted date
│   │       ├── nav-links.tsx         # Top navigation
│   │       ├── brand-logo.tsx        # Project branding
│   │       └── site-background.tsx   # Dark background
│   │
│   ├── lib/                          # Pure functions (unit-tested with vitest)
│   │   ├── api.ts                    # Fetch + types, apiFetch wrapper
│   │   ├── live.ts                   # liveMinute interpolation (tested)
│   │   ├── results.ts                # Dedupe/group recent results (tested)
│   │   ├── stakes.ts                 # Fixture stakes + scenario guards
│   │   ├── time.ts                   # Australia/Melbourne formatting
│   │   ├── sparkline.ts              # SVG path generation (tested)
│   │   └── types.ts                  # Shared types (Brief, Standing, Fixture, etc.)
│   │
│   ├── public/
│   │   ├── CHANGELOG.md              # Static changelog (parsed in /changelog)
│   │   └── favicon.ico
│   │
│   ├── app/globals.css               # Tailwind + design tokens (CSS custom properties)
│   ├── next.config.ts                # output: "standalone", env vars
│   ├── tailwind.config.ts            # Tailwind v4 + @tailwindcss/postcss
│   ├── tsconfig.json                 # TypeScript strict mode
│   ├── package.json                  # React 19.2.4, Next 16.2.9, dependencies
│   ├── package-lock.json
│   ├── .eslintrc.json                # ESLint 9 (strict)
│   └── .env.example
│
├── infra/                            # Operations + provisioning (Shell/Python)
│   ├── provision-vm.sh               # Create Azure VM (B2als_v2, Docker, NSG)
│   ├── cost-guardrails.sh            # Budget alerts ($20/mo limit)
│   ├── Caddyfile                     # TLS reverse proxy config
│   └── .gitkeep
│
├── prototypes/                       # Static design mockups (NOT deployed)
│   ├── README.md                     # Screen index (s01–s10, s08-forecast-compare)
│   ├── s01-brief-list.html           # Home (brief list + standings)
│   ├── s02-brief-detail.html         # Brief markdown
│   ├── s03-standings.html            # Group tables + trend
│   ├── ... (more screen HTML files)
│   ├── components.css                # Component styles
│   ├── interactions.js               # Client-side interactivity
│   └── index.html
│
├── docs/
│   ├── deployment.md                 # Full deploy runbook (VM setup, CI/CD, secrets)
│   └── AGENTS.md                     # Claude Code guidelines
│
├── ck_docs/                          # Knowledge base (this documentation set)
│   ├── diagrams/
│   │   ├── architecture.drawio       # Editable diagram (draw.io)
│   │   ├── architecture.svg          # Rendered architecture
│   │   └── architecture.png          # Static reference
│   ├── journal/                      # Implementation journals (phase notes)
│   │   ├── 2026-06-19-*.md           # Various phase completion notes
│   │   └── ...
│   ├── UI_SPEC.md                    # Design system + screen specs (CANONICAL)
│   ├── project-overview-pdr.md       # (THIS FILE SET)
│   ├── system-architecture.md
│   ├── codebase-summary.md
│   ├── code-standards.md
│   ├── project-roadmap.md
│   ├── deployment-guide.md
│   └── design-guidelines.md
│
├── ck_plans/                         # Implementation plans (phase-based)
│   └── 260621-azure-vm-deploy/
│       ├── plan.md
│       └── ...
│
├── .github/
│   └── workflows/
│       └── deploy.yml                # CI/CD: test → build → push GHCR → SSH deploy
│
├── docker-compose.yml                # Base services (postgres, backend, frontend, migrate)
├── docker-compose.override.yml       # Dev overlay (host ports, bind-mounts)
├── docker-compose.prod.yml           # Prod overlay (GHCR images, Caddy, no host ports)
├── Dockerfile (backend)              # Python 3.12 + uv
├── Dockerfile (frontend)             # Node 20 + next build → standalone
│
├── .env.example                      # Template (API_FOOTBALL_KEY, DEEPSEEK_API_KEY, etc.)
├── .gitignore                        # .env, node_modules, __pycache__, .next, db.sqlite
├── README.md                         # Project overview + quick start
├── CLAUDE.md                         # IPA workflow guidelines
└── LICENSE

```

---

## 2. Backend (Python)

### Dependencies

**Core Stack:**
- `fastapi>=0.115` — Web framework
- `uvicorn` — ASGI server
- `sqlalchemy[asyncio]~=2.0` — **Core** (not ORM)
- `alembic>=1.13` — Migrations
- `psycopg[binary]~=3.2` — PostgreSQL driver
- `pydantic[email]>=2.0` — Data validation + settings
- `pydantic-settings>=2.0` — Environment config
- `httpx>=0.25` — Async HTTP client
- `pytz` — Timezone handling
- `langgraph>=0.2` — State graph (Collector → Analyst → Editor)
- `langchain-core>=0.2` — LLM abstraction
- `langchain-openai>=0.2` — DeepSeek (OpenAI-compatible)

**Testing & Dev:**
- `pytest>=7.0` — Test framework
- `pytest-asyncio` — Async test support
- `pytest-cov` — Coverage reporting

**Version Constraints:**
- Python >=3.12
- PostgreSQL 16+
- Docker Compose v2+

### Code Organization

**Patterns:**
- **Pure functions:** `standings_math.py`, `api_football.py` (parsers) — testable, no side effects
- **SQLAlchemy Core:** Table objects, explicit `insert()`, `update()`, `delete()` queries
- **Async I/O:** FastAPI routes are async; DB calls use psycopg async adapter (or sync on thread pool)
- **Upserts:** Non-fatal on conflict; keeps last-good brief if new one fails
- **Retry logic:** DeepSeek calls retry 3x w/ exponential backoff (exceptions logged)
- **Logging:** QueueHandler + DB persistence; whitelisted context (node, attempt, fixture_id, brief_date)

### Key Algorithms

**Standings Computation** (`data/standings_math.py`):
```python
def compute_group_table(matches: list[Match]) -> list[TeamRow]:
    # 1. For each team: count W/D/L, sum 3/1/0 points
    # 2. Tiebreak: points → GD (goal difference) → GF (goals for)
    # 3. Return sorted by tiebreak
    # Note: FIFA H2H not implemented (V1 limitation); can be added post-tournament

def rank_best_thirds(groups: dict[str, list[TeamRow]]) -> list[TeamRow]:
    # 1. For each group, take 3rd-place team
    # 2. Sort all thirds by points → GD → GF
    # 3. Return top 8 (12-group format: 4 qualify, 8 fill 2 spots)

def qualification_status(groups, best_thirds) -> dict[str, str]:
    # Return per-team status: "Qualified", "Eliminated", "TBD", "Qualification Playoff"
```

**Live Polling** (`pipeline/live_poller.py`):
- Query API-Football `/fixtures?live=all` every 120s
- For each live fixture, update `matches.score`, `status`, `elapsed`
- Sleep 300s between polls if no match in-play window

---

## 3. Frontend (TypeScript + React)

### Dependencies

**Core Stack:**
- `next@16.2.9` — Framework (App Router, SSR)
- `react@19.2.4` — Library
- `typescript@5` — Language (strict mode)
- `tailwindcss@v4` — CSS framework
- `@tailwindcss/postcss` — PostCSS plugin
- `react-markdown@10` — Markdown → JSX
- `rehype-sanitize@6` — XSS protection

**Client Libraries:**
- `date-fns` — Date formatting (alternative: Intl API for AEST)

**Testing & Dev:**
- `vitest@2` — Test runner (lib/ functions only)
- `eslint@9` — Linting (strict)

**Versions:**
- Node.js 20+
- npm 10+

### Code Organization

**Patterns:**
- **Server-first:** Page components are server components by default
- **Client islands:** Only `LiveMatchCard`, `LogsView` are `"use client"`
- **API wrapper:** `lib/api.ts` centralizes all fetches; returns null on error
- **Type safety:** Pydantic response models matched by TypeScript interfaces
- **Hydration safety:** `suppressHydrationWarning` on time/date components; fallback UI for TBD
- **Styling:** Tailwind classes + CSS custom properties (design tokens in `globals.css`)
- **Error boundaries:** Empty-state fallbacks for missing data

### Key Utilities

**`lib/live.ts` — Interpolate elapsed time:**
```typescript
function liveMinute(baseMinute: number, baseFetchTime: number, now: number): number {
  // Interpolate elapsed time between API updates (30s apart)
  // Prevents jerky updates on low-frequency polls
}
```

**`lib/results.ts` — Deduplicate and group recent results:**
```typescript
function groupRecentResults(matches: Match[]): Map<string, Match[]> {
  // Group by date; dedupe by fixture_id
}
```

**`lib/sparkline.ts` — SVG trend chart:**
```typescript
function generateSparkline(points: number[]): string {
  // Returns SVG path for position-delta chart
}
```

**`lib/time.ts` — Australia/Melbourne formatting:**
```typescript
function formatTimeAEST(date: Date): string {
  // Format with AEST offset; fallback if timezone unavailable
}
```

### Components

**Server components:** Page layouts, data fetching
**Client components:** Polling, user interaction, state
**Primitives:** Reusable UI building blocks (flags, badges, cards)

---

## 4. Infrastructure & Deployment

### Docker Compose

**Base services** (`docker-compose.yml`):
- `postgres:16-alpine` — Database
- `backend` — FastAPI + scheduler + live_poller
- `frontend` — Next.js standalone
- `migrate` — One-shot Alembic + seed

**Dev overlay** (`docker-compose.override.yml`):
- Host ports: 5432, 8000, 3000
- Bind-mounts: `backend/`, `frontend/`
- Frontend target: `dev` (hot reload via `npm run dev`)

**Prod overlay** (`docker-compose.prod.yml`):
- Pulls images from `ghcr.io/phucsystem/wc2026-{backend,frontend}`
- Adds Caddy reverse proxy (port 443/80)
- No host ports except Caddy

### CI/CD (.github/workflows/deploy.yml)

1. **Test job:** `pytest` + `npm test` + `next build` (runs on PR + push)
2. **Build-push job:** Buildx images → ghcr.io (on push to main only)
3. **Deploy job:** SSH to VM, `git pull`, `docker compose pull`, `up -d` (gated by DEPLOY_ENABLED variable)

**Secrets:** SSH_HOST, SSH_USER, SSH_PRIVATE_KEY, AZURE_CREDENTIALS, AZURE_RESOURCE_GROUP, AZURE_NSG_NAME

### VM Provisioning (infra/provision-vm.sh)

- Creates Azure RG + VM (Standard_B2als_v2, Ubuntu 22.04)
- Installs Docker + Compose via cloud-init
- Creates NSG (80/443 inbound, 22 from operator IP)
- Preflights SKU availability; suggests alternatives

### TLS (Caddyfile)

- Reverse proxy: all traffic → frontend:3000
- Auto Let's Encrypt (requires DNS name)
- Rejects `/api/*` from public (backend internal-only)

---

## 5. Testing Strategy

### Backend (pytest)

| Module | Test File | Coverage |
|--------|-----------|----------|
| `standings_math` | `test_standings_math.py` | Group tables, best-thirds, qualification logic |
| `api_football` | `test_api_football.py` | Parser quirks (aggregate block, fixture shaping) |
| `scheduler` | `test_scheduler.py` | DST logic, timezone handling |
| `fixtures` | `test_fixtures.py` | Fixture shaping, status transitions |
| `live_poller` | `test_live_poller.py` | Polling intervals, in-play detection |

**Known gaps:** Limited network mocking; LLM-node tests stubbed (hard to mock OpenAI).

### Frontend (vitest)

| Module | Test File | Coverage |
|--------|-----------|----------|
| `lib/live.ts` | `lib/live.test.ts` | Time interpolation |
| `lib/results.ts` | `lib/results.test.ts` | Deduplication, grouping |
| `lib/sparkline.ts` | `lib/sparkline.test.ts` | SVG path generation |

**Known gaps:** No component tests; no E2E tests (low churn expected post-MVP).

---

## 6. Known Gaps

| Gap | Severity | Rationale |
|-----|----------|-----------|
| No GraphQL (REST API only) | Low | REST sufficient for query patterns; GraphQL adds complexity |
| No WebSocket (polling only) | Low | 30s polling + client interpolation acceptable for MVP |
| Qualification status computed but not in UI | Medium | Persisted in articles.intelligence JSONB; can surface later |
| Knockout bracket stubbed | Medium | Requires group-stage completion; low priority until then |
| No component/E2E tests (frontend) | Medium | Manual QA post-MVP sufficient for low-churn codebase |
| Changelog static (manual updates) | Low | Could auto-generate from git tags; low priority |
| H2H tiebreaker not implemented | Low-Medium | V1 uses GD→GF; can add post-tournament if needed |
| No dark/light theme toggle | Low | CSS tokens ready; toggle deferred to V2 |
| No user auth or personalization | N/A | Out of V1 scope |

---

## 7. File Size Reference

| Directory | LOC | Notes |
|-----------|-----|-------|
| `backend/app/` | ~2.8k | Core API, pipeline, data |
| `backend/tests/` | ~1.2k | Pytest suite |
| `backend/db/migrations/` | ~1.2k | Alembic migration files |
| `frontend/app/` + `components/` + `lib/` | ~5.2k | Pages, components, utilities |
| `frontend/public/` + `styles/` | ~0.8k | Assets, CSS |
| `infra/` | ~0.5k | Provisioning scripts |
| `prototypes/` | ~6k | Static mockups (not deployed) |
| **Total tracked** | **~18.7k** | Excludes node_modules, venv, .git |

---

## 8. Key Files Reference

| File | Purpose | Size |
|------|---------|------|
| `backend/app/main.py` | FastAPI app, routers | ~60 LOC |
| `backend/app/pipeline/graph.py` | LangGraph state machine | ~150 LOC |
| `backend/app/data/standings_math.py` | Deterministic logic | ~300 LOC |
| `backend/app/api/briefs.py` | Briefs endpoints | ~50 LOC |
| `frontend/app/page.tsx` | Home (server component) | ~80 LOC |
| `frontend/components/live-match-card.tsx` | Live polling client | ~120 LOC |
| `frontend/lib/api.ts` | API wrapper + types | ~100 LOC |
| `docker-compose.yml` | Base stack | ~50 LOC |
| `infra/provision-vm.sh` | VM provisioning | ~120 LOC |

---

## 9. References

- **README.md** — Quick start, local setup, deploy overview
- **System Architecture** (`ck_docs/system-architecture.md`) — Component deep-dive
- **Code Standards** (`ck_docs/code-standards.md`) — Conventions, patterns
- **Deployment Guide** (`ck_docs/deployment-guide.md`) — Ops runbook (cross-ref to docs/deployment.md)
- **Project Overview** (`ck_docs/project-overview-pdr.md`) — Product decisions, PDR
