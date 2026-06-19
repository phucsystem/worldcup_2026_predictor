# Phase 6 Implementation Report

## Phase
- Phase: 06-frontend-polish-azure-deploy
- Plan: ck_plans/260619-1030-world-cup-intelligence/
- Status: completed

## Files Modified

### New components
- `frontend/components/brief-card.tsx` — HeroBriefCard + CompactBriefCard (DRY extractions)
- `frontend/components/date-stamp.tsx` — DateStamp with fresh/past variants
- `frontend/components/empty-state.tsx` — reusable empty/error state
- `frontend/components/position-delta.tsx` — ▲/▼/– with aria-label (never color-only)
- `frontend/components/qualification-badge.tsx` — ●/○/✕ with aria-label + sr-only text

### Updated pages
- `frontend/app/page.tsx` — hero card, EARLIER 1/2/3 col grid, DateStamp, EmptyState, "View archive →"
- `frontend/app/brief/[date]/page.tsx` — back link, display headline clamp, prose markdown, provenance footer
- `frontend/app/standings/page.tsx` — QualificationBadge, EmptyState, snapshot label, knockout stub
- `frontend/app/archive/page.tsx` — EmptyState, aria-labels on rows
- `frontend/app/globals.css` — prose-brief styles, focus-visible ring, prefers-reduced-motion

### Updated components
- `frontend/components/standings-table.tsx` — uses PositionDelta + QualificationBadge, hover row, sticky minWidth, semantic section/aria-label

### IaC
- `backend/Dockerfile.api` — production API image (identical to Dockerfile; added for explicit naming)
- `frontend/Dockerfile` — multi-stage node:24-alpine builder + runner, standalone output
- `frontend/next.config.ts` — added `output: "standalone"`
- `infra/main.bicep` — top-level orchestrator; wires postgres + container-apps + job modules
- `infra/postgres.bicep` — Burstable B1ms Flexible Server, worldcup DB, firewall for Azure services
- `infra/container-apps.bicep` — Log Analytics + CA Env + ACR ref + API app (internal) + frontend (public)
- `infra/container-app-job.bicep` — REWRITTEN: replaced invalid `keyVaultUrl: 'ref:...'` stubs with `@secure()` value params matching container-apps.bicep pattern
- `.github/workflows/deploy.yml` — optional CI (disabled by `if: false` guards)
- `README.md` — Deploy to Azure runbook section added

## Verification Outputs

### Frontend build (`npm run build`)
```
Route (app)
┌ ƒ /
├ ○ /_not-found
├ ƒ /archive
├ ƒ /brief/[date]
└ ƒ /standings

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```
Build: PASS

### TypeScript (`tsc --noEmit`)
No output = no errors. PASS

### Backend tests (`pytest`)
```
30 passed, 1 warning in 0.24s
```
PASS

### Bicep syntax (self-review — az unavailable)
- All 4 files: brace balance OK (opens == closes)
- Resource types: all valid ARM provider strings with pinned API versions
- `@secure()` on every secret param in all 4 files
- No hardcoded secret values (grep scan clean)
- Module param names match module param declarations
- Fixed Phase 5 bug: `container-app-job.bicep` had `keyVaultUrl: 'ref:...'` — replaced with direct `@secure()` value params

### Secret audit
- No hardcoded secrets in any infra file
- All secrets flow as `@secure()` Bicep params → Container Apps `secrets[].value` → env via `secretRef`
- CI workflow uses GitHub Actions secrets only

## No Live Azure Actions Taken
No `az login`, no `az deployment`, no resource creation. IaC files are write-only artifacts for the user to deploy.

## Issues / Deviations
1. `az` CLI not installed on this machine — Bicep validated by self-review only (brace balance + ARM type strings + param reference tracing). Recommend user runs `az bicep build --file infra/main.bicep` before first deploy.
2. `container-app-job.bicep` (Phase 5 file) had invalid `keyVaultUrl: 'ref:...'` secret syntax — fixed to `@secure()` value params. This is a correctness fix, not a scope change.
3. `next.config.ts` `output: 'standalone'` — build confirmed passing. The standalone output bundles `server.js` + minimal node_modules into `.next/standalone`; the Dockerfile COPY path is correct.
4. Qualification status derived from position rank (≤2 = qualified, last = eliminated, else contention) — heuristic for group stage. Real qualification logic (3-team groups in WC2026) would need backend field; flagged for future refinement.

**Status:** DONE
**Summary:** All frontend components, pages, Dockerfiles, Bicep IaC, CI workflow, and README runbook implemented. Build, typecheck, and 30 backend tests all pass. No Azure actions taken.
**Concerns:** Bicep syntax review-only (no az CLI). Qualification badge uses positional heuristic.
