#!/usr/bin/env bash
# Phase 3 — provision the single VM (idempotent-ish; safe to re-run for missing bits).
# Creates the resource group, a B1ms Ubuntu VM with Docker (via cloud-init), and an
# NSG that allows 80/443 from anywhere and 22 only from your current public IP.
#
# Usage:
#   API_FOOTBALL_KEY=... DEEPSEEK_API_KEY=... ./infra/provision-vm.sh
# Override defaults via env: RG, LOCATION, VM_NAME, VM_SIZE, ADMIN_USER, SPOT=1
set -euo pipefail

RG="${RG:-rg-wc2026-prod}"
LOCATION="${LOCATION:-australiaeast}"
VM_NAME="${VM_NAME:-vm-wc2026}"
VM_SIZE="${VM_SIZE:-Standard_B1ms}"
ADMIN_USER="${ADMIN_USER:-azureuser}"
IMAGE="${IMAGE:-Ubuntu2204}"
DISK_GB="${DISK_GB:-30}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v az >/dev/null || { echo "az CLI not found"; exit 1; }
az account show >/dev/null || { echo "Run 'az login' first"; exit 1; }

MY_IP="$(curl -fsS https://api.ipify.org)"
echo ">> Provisioning $VM_NAME ($VM_SIZE) in $RG / $LOCATION; SSH locked to $MY_IP"

az group create -n "$RG" -l "$LOCATION" -o none

SPOT_ARGS=()
if [[ "${SPOT:-0}" == "1" ]]; then
  SPOT_ARGS=(--priority Spot --eviction-policy Deallocate --max-price -1)
  echo ">> Spot enabled (eviction: Deallocate)"
fi

az vm create \
  -g "$RG" -n "$VM_NAME" \
  --image "$IMAGE" --size "$VM_SIZE" \
  --admin-username "$ADMIN_USER" \
  --generate-ssh-keys \
  --os-disk-size-gb "$DISK_GB" \
  --storage-sku StandardSSD_LRS \
  --custom-data "$HERE/cloud-init.yaml" \
  --public-ip-sku Standard \
  --nsg-rule NONE \
  "${SPOT_ARGS[@]}" \
  -o table

# NONE above means the auto-created NSG has no inbound allow rules; we add exactly
# the ones we want. SSH is locked to your current IP (the ONLY port-22 rule).
az network nsg rule create -g "$RG" --nsg-name "${VM_NAME}NSG" \
  -n allow-ssh-myip --priority 1000 --access Allow --protocol Tcp \
  --direction Inbound --destination-port-ranges 22 \
  --source-address-prefixes "${MY_IP}/32" -o none
az network nsg rule create -g "$RG" --nsg-name "${VM_NAME}NSG" \
  -n allow-web --priority 1010 --access Allow --protocol Tcp \
  --direction Inbound --destination-port-ranges 80 443 \
  --source-address-prefixes Internet -o none

PUBLIC_IP="$(az vm show -d -g "$RG" -n "$VM_NAME" --query publicIps -o tsv)"
echo ""
echo ">> VM ready. Public IP: $PUBLIC_IP"
echo ">> Next:"
echo "   1. Point your DNS A record (or use ${PUBLIC_IP//./-}.sslip.io) at $PUBLIC_IP"
echo "   2. ssh ${ADMIN_USER}@${PUBLIC_IP}"
echo "   3. git clone the repo, create .env (see docs/deployment.md), then run the deploy workflow"
echo "   4. GitHub secrets: SSH_HOST=$PUBLIC_IP  SSH_USER=$ADMIN_USER  SSH_PRIVATE_KEY=~/.ssh/id_rsa"
