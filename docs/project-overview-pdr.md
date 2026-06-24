# Project Overview and Product Decision Record

**Project:** World Cup 2026 Intelligence  
**Current State:** MVP launched (daily automated intelligence service)  
**Date Last Updated:** 2026-06-21

---

## 1. Product Vision

An **automated, deterministic daily intelligence service** for FIFA World Cup 2026. Each morning at 7:00 AM Australia/Melbourne, the system:

1. **Collects** live fixtures and standings from API-Football
2. **Computes** all group tables, qualification status, and tournament statistics deterministically in Python (unit-tested, no LLM randomness)
3. **Narrates** the pre-computed facts via a 3-node LangGraph pipeline (DeepSeek LLM in structured json_mode)
4. **Publishes** an editorial brief to the Next.js dashboard, plus standings tables and live fixture tracking

**Core principle:** Numbers are ground truth; the LLM only articulates facts, never invents stats or predictions.

---

## 2. Success Criteria

| Criterion | Status | Notes |
|-----------|--------|-------|
| Daily brief generation at scheduled time | ✅ Done | Runs at 20:00 & 21:00 UTC (7:00 AM AEST, DST-aware) |
| Deterministic standings math (unit-tested) | ✅ Done | Pure Python; 3/1/0 pts, tiebreak GD→GF; FIFA H2H omitted in V1 |
| API-Football integration without failures | ✅ Done | Handles aggregate-block quirk; graceful degradation on missing keys |
| DeepSeek LLM pipeline (collector→analyst→editor) | ✅ Done | json_mode, 3 retries w/ exponential backoff; cost/token tracking |
| Next.js dashboard (SSR, responsive) | ✅ Done | Server-first with client islands; Australia/Melbourne timezone anchored |
| PostgreSQL persistence (Alembic, upserts) | ✅ Done | 6 migrations; non-fatal upserts; snapshot-based standings |
| Logging + observability (app_logs table) | ✅ Done | Non-blocking QueueHandler; INFO+ persisted; 14-day retention |
| Single-VM deployment (Azure, Caddy TLS) | ✅ Done | docker-compose stack; GHCR images; NSG + SSH JIT access |

---

## 3. Product Decisions (PDR)

### 3.1 Architecture: Single-Stage Monolithic Service

**Decision:** One `docker-compose` stack (postgres + backend + scheduler + frontend + caddy) on a single Azure B2als_v2 VM (2 vCPU/4 GiB).

**Rationale:**
- MVP scope does not require scaling beyond 1 brief/day and steady-state ~100 concurrent users.
- Simplifies deployment, secrets management, and operational observability.
- Burstable VM ($15–20/mo) fits early product stage.

**Trade-off:** If traffic/frequency grows 10x, split into microservices (separate API, scheduler, frontend) and scale Postgres.

---

### 3.2 Data: Deterministic Python + LLM Narration

**Decision:** All group tables, qualification status, and tournament summary computed deterministically in Python (`standings_math.py`); the LLM only narrates these facts in json_mode.

**Rationale:**
- Reproducible, auditable, unit-tested logic reduces liability and user trust issues.
- Separates concerns: product data (Python) from editorial narrative (LLM).
- Allows safe fact-checking: "does the brief cite only numbers we computed?"

**Trade-off:** LLM cannot invent novel insights (e.g., "team X is underperforming vs historical average" if not pre-computed). Mitigated by pre-computing storylines (qualification stakes, group scenarios, power ranking) that the LLM annotates.

---

### 3.3 Briefing Frequency: Daily at 7:00 AM AEST

**Decision:** Schedule runs at 20:00 & 21:00 UTC, with a DST guard, so they fire once per day at 7:00 AM Australia/Melbourne.

**Rationale:**
- Morning delivery aligns with user persona (P-01: "one daily catch-up"); avoids real-time pressure.
- Caps API-Football quota and DeepSeek spend (~1 call/day).
- Simpler scheduler logic than live-feed model.

**Trade-off:** Users miss live match events between 7 AM and next day. Mitigated by `live_poller.py` updating scores every 2 minutes during in-play fixtures (within 3h of kickoff).

---

### 3.4 Frontend: Next.js 16 Server-First SSR

**Decision:** Next.js App Router, server-first rendering, client islands for live match updates and log search.

**Rationale:**
- SSR ensures SEO and fast First Contentful Paint (important for trust/credibility).
- Minimal client JS; live polling isolated to `LiveMatchCard` + `LogsView`.
- API calls never reach the browser (all via Next route handlers); backend URL opaque to users.
- Tailwind + rehype-sanitize for consistent styling and XSS safety.

**Trade-off:** No SPA-style instant navigation. Browser-based dev-server mode exists for quick local iteration; prod uses standalone build.

---

### 3.5 Database: Snapshot-Based Standings (Not a Time Series)

**Decision:** `standings` table stores one row per date per group; no intra-day snapshots.

**Rationale:**
- Aligns with daily brief cadence; avoids unnecessary storage and query complexity.
- Simplifies UI: standings at date X are deterministic, no "which snapshot of day X?"

**Known limitation:** Cannot render "standings as they were at 3 PM on June 21" (only "standings computed after June 21 fixture results"). Acceptable for current product scope.

---

### 3.6 API Authentication: Local/Dev Only, No Auth

**Decision:** POST `/api/admin/collect` and `/api/admin/run-brief` endpoints are unauthenticated, intended for local/dev use only.

**Rationale:**
- Early product stage; manual trigger needed for testing and backfills.
- Reduces operational complexity during MVP.

**Security note:** Do NOT expose these endpoints on public ingress without auth. In prod, only the scheduler (internal container) calls them; browser never does.

---

### 3.7 Logs: Persistent, Queryable App Logs Table

**Decision:** Non-blocking async QueueHandler writes INFO+ events to `app_logs` with 14-day retention; available via GET `/api/logs` (with level/source/message filters).

**Rationale:**
- Helps diagnose pipeline failures and collector quirks (e.g., "why did today's brief miss a team?").
- QueueHandler prevents logging I/O from blocking request handling.
- Whitelisted context fields (node, attempt, fixture_id, brief_date) aid debugging without logging sensitive data.

---

### 3.8 Staging/Testing: Single Prod Instance, No Staging Environment

**Decision:** No separate staging VM. All tests run locally or in CI; prod is the sole deployed environment.

**Rationale:**
- Daily-cadence product doesn't justify dual infrastructure cost.
- Tests cover data ingestion and standings math thoroughly.
- Deployment is low-risk: `git pull --ff-only` + `docker compose pull` + `up -d` (blue-green via rolling containers).

**Risk:** If a deploy breaks prod, brief is delayed by up to 24h until rollback/fix. Mitigated by: branch protection (PR-required), CI tests run first, manual deploy gate (DEPLOY_ENABLED variable).

---

## 4. Known Gaps and Limitations

| Gap | Impact | Workaround / Planned |
|-----|--------|----------------------|
| Qualification status computed but not surfaced in UI | Low | Persisted in `intelligence` JSONB; UI can add a Standings tooltip or separate Qualification page later |
| Knockout bracket partially stubbed | Medium | Prototype s06 exists but not wired to fixture data; requires group-stage completion to be meaningful |
| No component / E2E tests (frontend) | Medium | Vitest covers `lib/` pure functions; manual QA for UI changes; low churn expected post-MVP |
| Changelog parsed from static file, not auto-generated | Low | Public commitment to change log manually; consider git-tag automation post-launch |
| API-Football free plan covers seasons 2021–2023 only; WC2026 requires paid plan | Medium | Demo uses `API_FOOTBALL_SEASON=2022` (Qatar 2022 real data); paid key reads 2026 live data |
| No user authentication or personalization | N/A | Out of V1 scope; global read-only view |
| No dark/light theme toggle (dark only) | Low | Design system supports light tokens; CSS theming ready; toggle deferred to V2 |
| H2H tiebreaker (FIFA rule) not implemented in standings math | Low-Medium | V1 uses GD→GF only; if two teams tied on pts+GD+GF, order is arbitrary. Real tournament will clarify ranking; can backfill post-tournament |

---

## 5. Team and Ownership

| Role | Owner | Notes |
|------|-------|-------|
| Product | Phuc DANG | Vision, user research, feature prioritization |
| Backend (Python, pipeline, data) | Phuc DANG | FastAPI, LangGraph, standings math, scheduler |
| Frontend (Next.js, dashboard) | Phuc DANG | SSR, components, API integration |
| Infra / Ops (Azure, Docker, CI/CD) | Phuc DANG | Provisioning, monitoring, deploy gates |

---

## 6. Success Metrics (Post-Launch)

- **Uptime:** Brief publishes on schedule ≥99% of days (≥363 days/year).
- **Data accuracy:** Standings match official FIFA tables ≥99% of matches.
- **User engagement:** Daily brief views, standing checks (analytics via Google Analytics tag).
- **Cost:** ≤$30/month (VM + API keys).
- **User feedback:** NPS ≥8 from 5+ engaged users.

---

## 7. Roadmap (Post-V1)

1. **Qualification UI:** Surface computed qualification status and advancement probabilities.
2. **Knockout bracket:** Wire live knockout predictions and results to UI.
3. **Personalization:** Save favorite teams; personalized email digest.
4. **Light theme:** Add dark/light toggle via CSS custom properties.
5. **Scalability:** Separate backend API, scheduler, frontend; horizontal scaling if traffic demands.
6. **H2H tiebreaker:** Implement FIFA head-to-head logic once rules are confirmed post-group-stage.

---

## 8. References

- **Architecture diagram:** `docs/diagrams/architecture.svg` (editable: `architecture.drawio`)
- **UI specification:** `docs/UI_SPEC.md` (design system, screen specs, user flows)
- **Deployment runbook:** `docs/deployment.md` (prod VM setup, CI/CD, secrets)
- **Code standards:** `docs/code-standards.md` (Python, TypeScript, SQL, testing)
- **System architecture:** `docs/system-architecture.md` (components, APIs, data flow)
- **Project journals:** `ck_docs/journal/` (phase notes, decisions, learnings)
