# Deployment — single Azure VM

The app ships **as-is** on one Azure burstable VM running the existing `docker-compose`
stack, fronted by Caddy for TLS. Images are built in GitHub Actions and pulled by the VM.

> Full rationale and decisions: [`ck_plans/260621-azure-vm-deploy/plan.md`](../ck_plans/260621-azure-vm-deploy/plan.md).

## What runs where

| Concern | File |
|---|---|
| Base stack (build, services, healthchecks) | `docker-compose.yml` |
| Local dev host ports (5432/8000/3000) | `docker-compose.override.yml` (auto-loaded) |
| Prod overlay (GHCR images, Caddy, internal-only backend/db) | `docker-compose.prod.yml` |
| TLS reverse proxy | `Caddyfile` |
| CI/CD (test → build → push GHCR → SSH deploy) | `.github/workflows/deploy.yml` |
| VM provisioning + ops scripts | `infra/` |

**Public surface = Caddy (:443) only.** In prod the `backend` (8000) and `postgres`
(5432) have no host ports — they are reachable only inside the compose network. The
browser never calls the backend (all `lib/api` access is server-side SSR).

- **Local dev:** `docker compose up` (base + override) — same ports as before.
- **Prod:** `docker compose -f docker-compose.yml -f docker-compose.prod.yml <cmd>` (no override).

## One-time setup

### 0. Prerequisites
- `az login`; region `australiaeast`.
- A DNS name for the VM (real domain, or a free `*.sslip.io` against the public IP) — required for Let's Encrypt.
- Keys ready: `API_FOOTBALL_KEY`, `DEEPSEEK_API_KEY`.

### 1. Provision the VM
```bash
./infra/provision-vm.sh          # B2als_v2 (2 vCPU/4 GiB) Ubuntu, Docker via cloud-init, NSG 80/443 + 22-from-your-IP
# gen1 B-series (B1ms/B2s) is often NotAvailableForSubscription; the script preflights
# the SKU and lists amd64 alternatives. Override with VM_SIZE=... if needed.
# Spot (cheaper, evictable):  SPOT=1 ./infra/provision-vm.sh
```
Note the printed public IP; point your DNS at it.

### 2. GitHub secrets (Settings → Secrets → Actions)
| Secret | Value |
|---|---|
| `SSH_HOST` | VM public IP or DNS name |
| `SSH_USER` | **`azureuser`** — must be the user cloud-init added to the `docker` group |
| `SSH_PRIVATE_KEY` | private key matching the VM's authorized key |
| `AZURE_CREDENTIALS` | `az ad sp create-for-rbac --sdk-auth` JSON (deploy job uses it to open SSH just-in-time) |
| `AZURE_RESOURCE_GROUP` | `rg-wc2026-prod` (or your `RG`) |
| `AZURE_NSG_NAME` | `vm-wc2026NSG` (i.e. `${VM_NAME}NSG`) |
| `DEPLOY_DIR` *(optional)* | repo path on VM (default `~/worldcup_2026_predictor`) |

The deploy job adds the runner's IP to the NSG for the duration of the SSH deploy, then
removes it — SSH stays locked to your IP otherwise. App secrets are **not** in CI; they
live in the VM `.env` (next step).

### 3. Bootstrap the VM
```bash
ssh azureuser@<public-ip>
git clone https://github.com/phucsystem/worldcup_2026_predictor.git
cd worldcup_2026_predictor
cp .env.example .env && nano .env     # set the values below
```
VM `.env` (git-ignored):
```
API_FOOTBALL_KEY=...
DEEPSEEK_API_KEY=...
BRIEF_TIMEZONE=Australia/Melbourne
SCHEDULER_INTERVAL_SECONDS=21600      # 6h — caps DeepSeek/API-Football spend
SITE_ADDRESS=wc2026.example.com       # the public hostname Caddy serves
```
First boot (or just trigger the workflow):
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
`migrate` runs Alembic once, then backend/scheduler/frontend/caddy start.

> **GHCR images must exist and be pullable first.** They're built by the first
> successful `main` CI run. New GHCR packages are **private by default**, so a plain
> `docker compose pull` returns `error from registry: denied`. After the first push,
> make both packages public once: GitHub → your profile → **Packages** →
> `wc2026-backend` / `wc2026-frontend` → Package settings → **Change visibility → Public**.
> (Keep them private instead? Then `docker login ghcr.io` with a read-only PAT on the VM.)
>
> For purely **local** testing you don't need GHCR at all — build locally:
> `docker compose up --build` (base + dev override, no prod overlay).

## Deploys
Push to `main` → CI runs tests → builds & pushes `ghcr.io/phucsystem/wc2026-{backend,frontend}`
→ SSHes to the VM and runs `git pull` + `compose pull` + `up -d`. PRs run tests only.

> The deploy does `git pull --ff-only`, so **don't edit tracked files on the VM** — any
> local override goes in `.env` (git-ignored). A diverged working tree fails the deploy.

## Seed & verify
```bash
./infra/seed.sh            # one pipeline run for today (or pass a date)
```
Confirm home / standings / fixtures / archive / changelog render with real data and the
scheduler produces the next refresh.

## Cost guardrails & ops
```bash
ALERT_EMAIL=you@example.com ./infra/cost-guardrails.sh   # $20/mo budget alert
```
- Free uptime monitor (e.g. UptimeRobot) on the public URL.
- **Off-window:** `az vm deallocate -g rg-wc2026-prod -n vm-wc2026` (pay only disk); `az vm start ...` to resume. If the IP changes, refresh the DNS A record / `SSH_HOST`.
- **Backup (convenience):** add `infra/pg-backup.sh` to cron (daily). Data is regenerable, so this is not DR.
