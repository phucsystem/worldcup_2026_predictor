# Deployment Guide (Operational Summary)

**Project:** World Cup 2026 Intelligence  
**Scope:** Quick operations reference; full runbook at `docs/deployment.md`  
**Last Updated:** 2026-06-21

---

## 1. Quick Reference

| Concern | Location | Details |
|---------|----------|---------|
| Full setup + troubleshooting | `docs/deployment.md` (canonical) | VM provisioning, CI/CD, secrets, rollback |
| Architectural decisions | `ck_plans/260621-azure-vm-deploy/plan.md` | Why single VM, cost, scaling trade-offs |
| Operational monitoring | `ck_docs/system-architecture.md` § 6 | Logs, metrics, health checks |
| Code standards | `ck_docs/code-standards.md` | Deployment-relevant patterns (secrets, env vars) |

**Start here:** If you're deploying for the first time, read `docs/deployment.md` end-to-end.

---

## 2. Deployment Overview

### 2.1 Architecture

**Single Azure VM (Standard_B2als_v2, 2 vCPU / 4 GiB, Ubuntu 22.04, australiaeast)**

```
Internet (HTTPS)
    ↓
Caddy (Port 443/80, auto Let's Encrypt)
    ↓
Next.js (Port 3000, internal)
    ↓
FastAPI (Port 8000, internal)
    ↓
PostgreSQL (Port 5432, internal)
    ↓
Disk (persistent volumes)
```

**No public backend URL.** Browser → Caddy → Next.js (SSR); Next.js → FastAPI (internal HTTP).

### 2.2 Services

| Service | Port | Visibility | Purpose |
|---------|------|-----------|---------|
| Caddy | 443/80 | Public | TLS proxy, auto Let's Encrypt |
| Next.js | 3000 | Internal | Frontend (SSR) |
| FastAPI | 8000 | Internal | API (read-only + admin triggers) |
| PostgreSQL | 5432 | Internal | Data persistence |
| Scheduler | (async) | Internal | Triggers brief at 7:00 AM AEST |
| Live poller | (async) | Internal | Updates scores every 2 min (in-play) |

---

## 3. One-Time Setup

### 3.1 Prerequisites

```bash
# Local machine
az login
# region: australiaeast

# Gather:
- API_FOOTBALL_KEY (from API-Football.com)
- DEEPSEEK_API_KEY (from api.deepseek.com)
- DNS name for VM (real domain or free sslip.io)
```

### 3.2 Provision VM

```bash
./infra/provision-vm.sh
# Output: public IP, SSH command, resource group name
# Note the printed IP; point your DNS at it
```

**Script does:**
- Creates Azure RG + VM (B2als_v2)
- Installs Docker + Compose via cloud-init
- Creates NSG (80/443 open, 22 from your IP only)
- Preflight checks SKU availability

**Optional:** `SPOT=1 ./infra/provision-vm.sh` for cheaper evictable VM.

### 3.3 Set Up GitHub Secrets

Navigate to repo Settings → Secrets → Actions:

| Secret | Value | Example |
|--------|-------|---------|
| `SSH_HOST` | VM public IP or DNS name | `1.2.3.4` or `wc2026.example.com` |
| `SSH_USER` | SSH username (always `azureuser`) | `azureuser` |
| `SSH_PRIVATE_KEY` | Private key matching authorized_keys | (paste full key, including `-----BEGIN`) |
| `AZURE_CREDENTIALS` | JSON from `az ad sp create-for-rbac --sdk-auth` | (json object) |
| `AZURE_RESOURCE_GROUP` | Resource group name | `rg-wc2026-prod` |
| `AZURE_NSG_NAME` | NSG name (format: `${VM_NAME}NSG`) | `vm-wc2026NSG` |

Then enable deploys:
```bash
gh variable set DEPLOY_ENABLED --body true
```

### 3.4 Bootstrap the VM

```bash
ssh azureuser@<IP>
git clone https://github.com/phucsystem/worldcup_2026_predictor.git
cd worldcup_2026_predictor

# Create .env
cp .env.example .env
nano .env
```

**Required in `.env`:**
```
API_FOOTBALL_KEY=<your-key>
DEEPSEEK_API_KEY=<your-key>
BRIEF_TIMEZONE=Australia/Melbourne
SCHEDULER_INTERVAL_SECONDS=21600
SITE_ADDRESS=<your-domain>
```

### 3.5 First Boot

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**What happens:**
1. `migrate` container runs Alembic (one-shot, then exits)
2. `postgres` starts with healthcheck
3. `backend` waits for postgres; starts scheduler + live poller
4. `frontend` waits for backend; starts Next.js
5. `caddy` reverse-proxies public traffic to frontend

**Verify:**
```bash
# From local machine
curl -I https://<your-domain>   # Should return 200 OK

# Or
docker compose logs -f frontend # See startup logs
```

---

## 4. Deployments (Ongoing)

### 4.1 CI/CD Flow

1. **Push to `main`** (or merge PR)
2. **GitHub Actions runs:**
   - Test job: `pytest` + `npm test` + `next build`
   - Build-push job: Build images → `ghcr.io/phucsystem/wc2026-{backend,frontend}:sha-xxx`, `:latest`
   - Deploy job (if DEPLOY_ENABLED=true): SSH → `git pull --ff-only` → `docker compose pull` → `up -d`

### 4.2 Manual Deploy

```bash
ssh azureuser@<IP>
cd worldcup_2026_predictor
git pull --ff-only
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 4.3 Deployment Safety

**Main branch is protected:** PR-required, tests run first.

**No direct file edits on VM.** Deploys use `git pull --ff-only` (fail if local commits exist).

**Rollback (if needed):**
```bash
git reset --hard <commit-hash>  # Revert to prior commit
docker compose down
docker compose pull
docker compose up -d
```

---

## 5. Secrets Management

### 5.1 API Keys (VM `.env` only, never in code)

```
# On VM
cat .env
# Shows:
API_FOOTBALL_KEY=...
DEEPSEEK_API_KEY=...
...
```

**Git-ignored.** Never committed.

### 5.2 GitHub Secrets (CI/CD only)

SSH and cloud credentials live in GitHub Actions Secrets (encrypted, not in repo).

**Never commit:**
- `.env` files
- `azure_credentials.json`
- SSH private keys
- Database dumps

### 5.3 Caddy TLS

**Automatic.** Caddy issues Let's Encrypt certificate on first `up -d`.

**Renewal:** Automatic (30 days before expiry).

---

## 6. Monitoring and Troubleshooting

### 6.1 Logs

**Container logs:**
```bash
docker compose logs -f backend       # FastAPI + scheduler
docker compose logs -f frontend      # Next.js
docker compose logs -f postgres      # Database
```

**App logs (via UI):**
Navigate to `/logs` in the dashboard; search by level, source, or message.

**App logs (via API):**
```bash
curl "http://localhost:8000/api/logs?level=ERROR&limit=20"
```

### 6.2 Health Check

```bash
# From VM
curl http://localhost:8000/health  # Should return {"status": "ok"}

# From local
curl https://<your-domain>/health  # Via Caddy (should also work)
```

### 6.3 Common Issues

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| Brief not generated at 7 AM | Check `docker compose logs backend` for scheduler errors | Verify BRIEF_TIMEZONE, SCHEDULER_INTERVAL_SECONDS, and system clock |
| Standings table empty | Check `docker compose logs backend` for API-Football errors | Verify API_FOOTBALL_KEY is set and has quota remaining |
| Images fail to pull from GHCR | `docker pull` returns "denied" | Make GHCR packages public: GitHub → Packages → wc2026-backend → Settings → Change visibility → Public |
| PostgreSQL won't start | Check `docker compose logs postgres` | Verify DATABASE_URL format; check disk space (`df -h`) |
| Caddy TLS fails | Check `docker compose logs caddy` | Verify SITE_ADDRESS is a valid DNS name; check port 80/443 open |

### 6.4 Cost Monitoring

**Budget alert:**
```bash
./infra/cost-guardrails.sh  # Sets up $20/mo alert
```

**Manual check:**
```bash
az consumption budget list -g rg-wc2026-prod
```

**Components:**
- VM (B2als_v2): ~$15–20/mo
- API-Football quota: ~$0–10/mo (depends on calls)
- DeepSeek LLM: ~$1–5/mo (1 brief/day, ~1000 tokens)
- **Total target:** ≤$30/mo

---

## 7. Scheduled Tasks

### 7.1 Brief Generation (7:00 AM AEST)

**Scheduler:** APScheduler, runs every 6 hours with DST guard.

**Trigger:** `POST /api/admin/run-brief?date=<YYYY-MM-DD>` (internal HTTP)

**Output:** Briefs table + articles JSONB + agent_runs metrics

**Monitoring:** Check `docker compose logs backend` for "Brief generated" or error messages.

### 7.2 Live Polling (During In-Play Matches)

**Poller:** Continuous background process.

**Behavior:**
- Every 120s, fetch `/fixtures?live=all` from API-Football
- Update match scores in DB
- Sleep 300s if no match in-play window (3 hours post-kickoff)

**Monitoring:** Check `docker compose logs backend` for "Live poll" messages.

---

## 8. Database Maintenance

### 8.1 Backups

**Current:** None (data can be re-collected from API-Football).

**Future:** Consider daily automated backups if this becomes a critical service.

### 8.2 Log Retention

**App logs:** Auto-purged at 14 days (configurable via `LOG_RETENTION_DAYS` in `.env`).

```sql
-- Manual cleanup (if needed)
DELETE FROM app_logs WHERE ts < NOW() - INTERVAL '14 days';
```

### 8.3 Migrations

**Auto-run on startup:** `migrate` container runs Alembic, then exits.

**Manual run (rare):**
```bash
docker compose exec backend alembic upgrade head
```

---

## 9. Scaling Considerations

**Current:** Single VM, daily brief, 1–2 requests/sec peak.

**If traffic grows 10x:**
- Separate backend API into own VM/container group
- Add Redis caching layer
- Horizontal scale Next.js with load balancer
- Move postgres to managed Azure Database for PostgreSQL

**Not needed yet.** Monitor monthly.

---

## 10. Disaster Recovery

### 10.1 Full VM Loss

**Recovery time:** 15 min (re-provision) + 5 min (redeploy).

**Steps:**
1. `./infra/provision-vm.sh` (new VM)
2. Point DNS to new IP
3. Set GitHub secrets (SSH_HOST, etc.)
4. Push to `main` (auto-deploys)

### 10.2 Data Loss

**Current:** No backup; briefs can be re-generated from API-Football.

**Standings:** Deterministically computed; re-run collector.

**Articles:** Lost (cannot re-generate same LLM output). Consider daily backups if critical.

---

## 11. Quick Commands Cheat Sheet

```bash
# Check status
docker compose ps
docker compose logs -f <service>

# Restart
docker compose restart backend
docker compose down && docker compose up -d

# SSH into VM
ssh azureuser@<IP>

# Manual brief trigger (from VM)
curl -X POST http://localhost:8000/api/admin/run-brief?date=$(date +%F)

# Data collection only
curl -X POST http://localhost:8000/api/admin/collect

# Health check
curl http://localhost:8000/health

# Cost check
az consumption budget list -g rg-wc2026-prod

# Upgrade DB schema
docker compose exec backend alembic upgrade head

# Scale VM (rare)
az vm resize --resource-group rg-wc2026-prod --name vm-wc2026 --size Standard_B4ms
```

---

## 12. Handoff Checklist

- [ ] SSH access to VM tested
- [ ] GitHub secrets configured (SSH_*, AZURE_*)
- [ ] DEPLOY_ENABLED set to `true`
- [ ] First deployment successful (check logs, frontend loads)
- [ ] Brief generated at 7:00 AM AEST
- [ ] Live score updates working
- [ ] Cost monitoring set up (budget alert)
- [ ] Operator trained on logs, rollback, SSH access
- [ ] Runbook (this doc + docs/deployment.md) reviewed

---

## 13. Support and Escalation

| Issue | Owner | Contact |
|-------|-------|---------|
| Prod VM down | Ops | Phuc DANG (phuc@travelstop.com) |
| Brief not generating | Data | Phuc DANG |
| UI broken | Frontend | Phuc DANG |
| Cost overruns | Finance | Phuc DANG |

---

## 14. References

- **Full runbook:** `docs/deployment.md` (definitive guide)
- **Architecture:** `ck_docs/system-architecture.md` (components, data flow)
- **Decisions:** `ck_plans/260621-azure-vm-deploy/plan.md` (why this approach)
- **Code standards:** `ck_docs/code-standards.md` (deployment-relevant patterns)
