#!/usr/bin/env bash
# Set ADMIN_PASSWORD on the production VM and recreate the frontend, via Azure
# CLI run-command (no SSH — goes through the VM agent, so it bypasses the NSG
# lock on port 22). Mirrors the .env sync in .github/workflows/deploy.yml.
#
# Usage:   ./infra/set-admin-password.sh
#          RG=... VM=... DEPLOY_DIR=... VM_USER=... ./infra/set-admin-password.sh
#
# Prereqs: `az login` done and the VM's subscription selected (`az account set`).
#
# Security:
#   - Password is read silently (read -rs): never in shell history or a file.
#   - It is base64-encoded before transit, so the literal does NOT appear in the
#     Azure Activity Log run-command record. base64 is obfuscation, not
#     encryption — assume anyone with log access can recover it, so rotate if it
#     leaks. The lower-exposure durable path is the GitHub Actions secret
#     ADMIN_PASSWORD (synced on deploy); use this script for an out-of-band set.
set -euo pipefail

RG="${RG:-rg-wc2026-prod}"
VM="${VM:-vm-wc2026}"
DEPLOY_DIR="${DEPLOY_DIR:-/home/azureuser/worldcup_2026_predictor}"
VM_USER="${VM_USER:-azureuser}"

command -v az >/dev/null || { echo "az CLI not found — install it and run 'az login' first." >&2; exit 1; }

if ! az vm show -g "$RG" -n "$VM" --query name -o tsv >/dev/null 2>&1; then
  echo "VM '$VM' not found in resource group '$RG' (subscription: $(az account show --query name -o tsv 2>/dev/null || echo '?'))." >&2
  echo "Override with RG=/VM= env vars, or list yours: az vm list -d -o table" >&2
  exit 1
fi

read -rs -p "New ADMIN_PASSWORD for $VM: " PW1; echo
read -rs -p "Confirm: " PW2; echo
[ -n "$PW1" ] || { echo "Empty password — aborting." >&2; exit 1; }
[ "$PW1" = "$PW2" ] || { echo "Passwords do not match — aborting." >&2; exit 1; }

PW_B64="$(printf '%s' "$PW1" | base64 | tr -d '\n')"
unset PW1 PW2

# Remote script: decode, swap ONLY the ADMIN_PASSWORD line (preserve the rest),
# fix ownership, recreate the frontend so it picks up the new env.
REMOTE=$(cat <<EOF
set -e
cd "$DEPLOY_DIR"
PW="\$(printf '%s' '$PW_B64' | base64 -d)"
tmp="\$(mktemp)"
grep -v '^ADMIN_PASSWORD=' .env 2>/dev/null > "\$tmp" || true
printf 'ADMIN_PASSWORD=%s\n' "\$PW" >> "\$tmp"
mv "\$tmp" .env
chown $VM_USER:$VM_USER .env
unset PW
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate frontend
echo "ADMIN_PASSWORD updated; frontend recreated."
EOF
)
unset PW_B64

echo "Applying to $VM ($RG) ..."
az vm run-command invoke -g "$RG" -n "$VM" \
  --command-id RunShellScript \
  --scripts "$REMOTE" \
  --query 'value[0].message' -o tsv

echo
echo "Done. Verify: log in at https://wc2026.phucsystemlabs.com/admin"
echo "If this password was ever shared in plaintext, rotate it — changing it auto-invalidates existing admin sessions."
