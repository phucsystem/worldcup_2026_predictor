# Project Roadmap

**Project:** World Cup 2026 Intelligence  
**Current Phase:** MVP (Launched)  
**Last Updated:** 2026-06-21

---

## 1. Current State (Shipped)

### Functional

- Daily brief generation (7:00 AM AEST) via LangGraph pipeline (Collector → Analyst → Editor)
- Deterministic group standings, qualification status, best-thirds computation (unit-tested)
- Live match score tracking (polling every 2 min during in-play fixtures)
- Next.js SSR dashboard with briefs, standings, fixtures, archive, logs views
- FastAPI read-only API + internal admin endpoints for data collection and brief triggering
- PostgreSQL persistence with Alembic migrations
- Docker Compose stack (local + prod with Caddy TLS)
- Single-VM Azure deployment with GitHub Actions CI/CD
- App logs with filtering, search, and 14-day retention

### Quality

- 80%+ test coverage on Python `standings_math.py` and `api_football.py`
- Server-first Next.js SSR with minimal client JS (islands: LiveMatchCard, LogsView)
- Non-blocking logging (QueueHandler) + graceful degradation (keep-last-good briefs)
- Type-safe (Python 3.12+ type hints, TypeScript strict mode)
- Branch-protected main with PR-required CI/CD

---

## 2. Known Gaps (V1 Limitations)

| Gap | Severity | Impact | Workaround |
|-----|----------|--------|-----------|
| Qualification status computed but not in UI | Medium | Users cannot see advancement probability | Persisted in `articles.intelligence` JSONB; can surface in v2 Qualification page |
| Knockout bracket partially stubbed (prototype exists) | Medium | No knockout predictions | Requires group-stage completion; low priority until June 22+ |
| No component/E2E tests (frontend) | Medium | UI regressions possible | Vitest covers `lib/` pure functions; manual QA acceptable for low-churn codebase |
| Changelog static (manual git updates) | Low | No auto-generated changelog | Could auto-generate from git tags; low priority |
| No dark/light theme toggle | Low | Dark-only (by design) | CSS tokens ready; toggle deferred to v2 |
| H2H tiebreaker not implemented | Low-Medium | Standings may differ from FIFA if GD+GF tied | V1 uses GD→GF only; can add post-group-stage if needed |
| No user auth / personalization | N/A | Global read-only view | Out of scope; consider for v2+ |

---

## 3. Post-Launch Work (Backlog)

### 3.1 Immediate (Week 1–2 post-launch)

**Priority: HIGH**

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| Monitor prod for 48h+ (logs, uptime, cost) | 2h/day | Ops | Catch any integration bugs; verify cost under $30/mo |
| Verify standings match official FIFA tables | 4h | Data | Spot-check 3+ groups; adjust H2H if needed |
| Gather user feedback (3+ engaged users) | 4h | Product | NPS, feature requests, pain points |
| Document learnings in ck_docs/journal/ | 2h | Engineering | Post-launch retrospective |

### 3.2 Short-term (Weeks 3–4)

**Priority: HIGH**

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| Qualification UI: Add qualification probability page | 8h | Frontend | Render computed qualification_status per team; show odds for advancing |
| Knockout bracket: Wire group-stage completion logic | 8h | Backend | Detect when group-stage ends; populate knockout fixture predictions |
| H2H tiebreaker: Implement if needed post-group-stage | 16h | Backend | Add head-to-head logic if FIFA-mandated and two teams tied on GD+GF |

### 3.3 Medium-term (Weeks 5–8)

**Priority: MEDIUM**

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| Email digest: Personalized daily brief delivery | 16h | Backend + Frontend | Opt-in email; summary + link to dashboard |
| Dark/light theme toggle | 8h | Frontend | Implement CSS variable swapping; persist user preference |
| User authentication: Social login (GitHub, Google) | 24h | Backend + Frontend | Enable personalization and saved favorites |
| Component tests: Add 50% coverage for key UI components | 12h | Frontend | Vitest for BriefCard, StandingsTable, LiveMatchCard |

### 3.4 Long-term (Post-Tournament)

**Priority: LOW**

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| Historical analysis: Compare actual vs pre-predicted outcomes | 20h | Data | Train model for future tournaments |
| Multi-language support (Spanish, Portuguese) | 32h | Frontend + i18n | Expand reach; deferred until v2 |
| Mobile app (React Native or Flutter) | 80h | Engineering | Native iOS/Android experience |
| Scalability: Microservices + horizontal scaling | 40h | Infra + Backend | Only if traffic demands (currently 1 brief/day) |
| Archive search / full-text indexing | 16h | Backend | Allow users to search past briefs by keywords |

---

## 4. Risk and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| API-Football free tier rate-limits us | Low | Brief generation delayed | Switch to paid plan ($10–50/mo); monitor quota daily |
| DeepSeek API latency or downtime | Medium | Brief delayed or failed | Implement circuit-breaker; keep last-good brief for 24h |
| Group-stage tiebreak not as GD→GF | Low-Medium | Standings incorrect | Add H2H logic post-announcement; re-compute historical briefs |
| Prod VM crashes / data loss | Low | 24h downtime; data loss | Daily automated backups; secondary replica (not done in v1) |
| User uploads malicious markdown to brief text | Low | XSS attack | rehype-sanitize already blocks scripts; audit LLM prompts quarterly |

---

## 5. Success Metrics (Post-Launch Targets)

| Metric | Target | Frequency | Owner |
|--------|--------|-----------|-------|
| **Uptime** | ≥99% (≥363 days/year brief publishes on schedule) | Daily | Ops |
| **Data accuracy** | Standings match official FIFA ≥99% | Weekly | Data |
| **User engagement** | ≥100 daily unique users + 50+ brief reads/day | Weekly | Analytics |
| **Cost** | ≤$30/month (VM + API keys) | Monthly | Finance |
| **Code health** | ≥80% test coverage on core modules | Per PR | Engineering |
| **User NPS** | ≥8/10 from 5+ engaged users | Monthly | Product |
| **Latency** | Brief generation <2 min, page load <1 sec | Per deployment | Ops |

---

## 6. Technical Debt

| Item | Effort | Priority | Notes |
|------|--------|----------|-------|
| Add async database adapter (psycopg async pool) | 8h | Medium | Currently sync on thread pool; minor but cleaner |
| Implement request correlation IDs | 4h | Low | Helps with log tracing; nice-to-have |
| Extract shared API types to OpenAPI spec | 6h | Low | Better API documentation; optional |
| Add APM (DataDog or similar) | 12h | Low | Monitor perf, errors; deferred until scale |
| Refactor pipeline state machine to be more testable | 8h | Low | LLM nodes are hard to unit-test; can improve |

---

## 7. Dependency Updates

**Monitoring cadence:** Monthly

| Dependency | Current | Risk | Notes |
|-----------|---------|------|-------|
| Next.js | 16.2.9 | Medium | v17 breaking changes; test before updating |
| FastAPI | ≥0.115 | Low | Stable; minor updates OK |
| SQLAlchemy | ~2.0 | Low | Stable Core API; safe |
| React | 19.2.4 | Medium | Check for SSR changes on major bumps |
| Tailwind | v4 | Medium | CSS custom property support new; test styling |
| Python | 3.12 | Low | EOL in Oct 2028; plan 3.13 migration in 2025 |

---

## 8. Roadmap Timeline

```
Jun 2026 (NOW)
├─ MVP launched (6/21)
└─ Immediate monitoring + user feedback (1–2 weeks)

Jul 2026 (Weeks 3–4)
├─ Qualification UI + Knockout bracket
└─ H2H tiebreaker (if needed)

Aug–Sep 2026 (Tournament in progress)
├─ Email digest
├─ Dark/light theme
├─ Auth (GitHub/Google)
└─ Component tests

Oct 2026 (Post-Tournament)
├─ Historical analysis
└─ Retrospective + v2 planning

2027+
├─ Multi-language
├─ Mobile app
├─ Scalability refactor
└─ Archive search
```

---

## 9. Decision Framework

**Feature acceptance criteria:**
1. Does it serve a user persona from UI_SPEC.md?
2. Is the effort proportional to impact?
3. Does it maintain ≥99% uptime?
4. Does it keep monthly cost ≤$50?

**If yes to all: Consider for next phase. If no: Defer or reject.**

---

## 10. References

- **Project overview:** `ck_docs/project-overview-pdr.md` (product decisions, principles)
- **System architecture:** `ck_docs/system-architecture.md` (deployment topology, APIs)
- **UI specification:** `ck_docs/UI_SPEC.md` (user personas, screen specs)
- **Code standards:** `ck_docs/code-standards.md` (implementation guidelines)
- **Deployment:** `docs/deployment.md` (prod setup runbook)
- **Previous learnings:** `ck_docs/journal/` (phase completion notes, blockers)

---

## 11. Contact and Ownership

| Role | Owner | Email |
|------|-------|-------|
| Product / Roadmap | Phuc DANG | phuc@travelstop.com |
| Engineering / Ops | Phuc DANG | phuc@travelstop.com |

**Questions?** Open an issue in the repo or reach out to Phuc.
