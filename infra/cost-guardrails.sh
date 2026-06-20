#!/usr/bin/env bash
# Phase 6 — $20/mo budget alert at 50/80/100%. Run after provisioning.
# Usage: ALERT_EMAIL=you@example.com ./infra/cost-guardrails.sh
# (Budget CLI shape varies by az version; if it errors, set this in the portal:
#  Cost Management -> Budgets -> Add, scope = the resource group, amount = 20.)
set -euo pipefail

RG="${RG:-rg-wc2026-prod}"
AMOUNT="${AMOUNT:-20}"
NAME="${NAME:-budget-wc2026}"
ALERT_EMAIL="${ALERT_EMAIL:?set ALERT_EMAIL=you@example.com}"

SUB_ID="$(az account show --query id -o tsv)"
START="$(date +%Y-%m-01)"
END="2027-01-01"

az consumption budget create \
  --budget-name "$NAME" \
  --amount "$AMOUNT" \
  --category Cost \
  --time-grain Monthly \
  --start-date "$START" \
  --end-date "$END" \
  --resource-group "$RG" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/$RG" \
  -o table

echo ">> Budget '$NAME' (\$$AMOUNT/mo) created on $RG."
echo ">> Add 50/80/100% notifications to $ALERT_EMAIL in the portal if not prompted by the CLI."
