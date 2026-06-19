---
phase: 6
title: "Frontend Polish & Azure Deploy"
status: code+IaC done; live Azure deploy pending (user creds)
priority: P2
effort: "2-3d"
dependencies: [4, 5]
---

# Phase 6: Frontend Polish & Azure Deploy

## Overview
Finish the public UI (brief list, detail, standings, archive) and ship the whole system to Azure Container Apps + Azure Postgres.

## Requirements
- Functional: public URL serves the daily brief; archive browsing; cron job runs in Azure producing daily briefs.
- Non-functional: responsive, accessible, secrets managed, reproducible IaC deploy.

## Architecture
### Frontend polish
- Home: hero + latest brief + recent list.
- Brief detail: typographic markdown, date, key outcomes.
- Standings: all 12 groups, position deltas, qualification badges.
- Archive: paginated brief history by date.
- Responsive Tailwind; basic a11y (semantic headings, contrast).

### Azure topology (IaC via Bicep)
- `Azure Database for PostgreSQL Flexible Server` (private or firewall-scoped).
- Container App: **FastAPI API** (always-on, min replicas 1).
- Container App: **Next.js SSR** (reads API; public ingress).
- Container Apps **Job**: pipeline (Phase 5 schedule).
- Secrets (`API_FOOTBALL_KEY`, `DEEPSEEK_API_KEY`, `DATABASE_URL`) via Container Apps secrets; consider managed identity for Postgres.
- Container registry (ACR) for the 3 images.

## Related Code Files
- Create: `infra/main.bicep`, `infra/postgres.bicep`, `infra/container-apps.bicep`, `frontend/components/*` (archive, brief-card, qualification-badge), `frontend/app/archive/page.tsx`, `backend/Dockerfile.api`, `frontend/Dockerfile`, `.github/workflows/deploy.yml` (optional CI)
- Modify: `frontend/app/*` (polish), `README.md` (deploy runbook)

## Implementation Steps
1. Build out UI components + archive page; responsive + a11y pass.
2. Dockerfiles for API + frontend; reuse `Dockerfile.job` from Phase 5.
3. Bicep: Postgres, ACR, 2 Container Apps + 1 Job, secrets, ingress.
4. Push images to ACR; deploy via Bicep; run migrations against Azure Postgres.
5. Smoke test: trigger job manually in Azure → brief appears on public URL.
6. (Optional) CI workflow for build+deploy on main.

## Success Criteria
- [ ] Public URL serves latest brief + archive + standings, responsive.
- [ ] Azure cron job produces a brief unattended in prod.
- [ ] Migrations applied to Azure Postgres; secrets not in images.
- [ ] End-to-end prod run verified (manual job trigger → live page updates).

## Risk Assessment
- Azure Postgres networking (private vs public) → start firewall-scoped public for speed, tighten later. Time-box.
- IaC drift / first-deploy friction → keep Bicep minimal; document manual steps in runbook.
- Cost → Postgres Flexible Server is the main spend; use Burstable tier (B1ms) for V1.
