#!/usr/bin/env bash
# Two helpers for the off-box X collection flow, both via Azure CLI run-command
# (no SSH — goes through the VM agent, bypassing the NSG lock on port 22).
# Mirrors infra/set-admin-password.sh.
#
#   ./infra/upload-x-candidates.sh --fetch-fixtures > fixtures.json
#       Print upcoming group-stage fixtures (id, home, away) in the social window,
#       as JSON, for feeding infra/collect-x-posts.py.
#
#   ./infra/upload-x-candidates.sh x_candidates.json
#       Upload a locally-collected x_candidates.json to the VM at
#       $DEPLOY_DIR/social-data/x_candidates.json, where the scheduler reads it
#       (SOCIAL_X_CANDIDATES_FILE in docker-compose.prod.yml). The next daily
#       collect curates the posts; no container restart needed.
#
# Prereqs: `az login` done and the VM's subscription selected.
set -euo pipefail

RG="${RG:-rg-wc2026-prod}"
VM="${VM:-vm-wc2026}"
DEPLOY_DIR="${DEPLOY_DIR:-/home/azureuser/worldcup_2026_predictor}"
VM_USER="${VM_USER:-azureuser}"
LOOKAHEAD_HOURS="${SOCIAL_LOOKAHEAD_HOURS:-48}"

command -v az >/dev/null || { echo "az CLI not found — install it and run 'az login'." >&2; exit 1; }

_run() {  # run a shell script on the VM, print its stdout
  az vm run-command invoke -g "$RG" -n "$VM" --command-id RunShellScript \
    --scripts "$1" --query 'value[0].message' -o tsv
}

if [ "${1:-}" = "--fetch-fixtures" ]; then
  # Pull upcoming, non-finished group-stage fixtures inside the social window.
  REMOTE=$(cat <<EOF
set -e
cd "$DEPLOY_DIR"
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T postgres \
  psql -U wc -d worldcup -tAc "SELECT COALESCE(json_agg(json_build_object('fixture_id',fixture_id,'home_team',home_team,'away_team',away_team)),'[]') FROM matches WHERE status NOT IN ('FT','AET','PEN') AND group_name IS NOT NULL AND kickoff_utc BETWEEN now() AND now() + interval '$LOOKAHEAD_HOURS hours';"
EOF
)
  # run-command wraps output with [stdout]/[stderr] banner lines (which also start
  # with '['), so match only a JSON array line — '[{...}]' or '[]' — not the banners.
  _run "$REMOTE" | grep -E '^\[(\{|\])' || { echo "No fixtures returned." >&2; exit 1; }
  exit 0
fi

FILE="${1:-}"
[ -n "$FILE" ] && [ -f "$FILE" ] || { echo "Usage: $0 <x_candidates.json> | --fetch-fixtures" >&2; exit 1; }
python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$FILE" \
  || { echo "$FILE is not valid JSON — aborting." >&2; exit 1; }

B64="$(base64 < "$FILE" | tr -d '\n')"
REMOTE=$(cat <<EOF
set -e
cd "$DEPLOY_DIR"
mkdir -p social-data
printf '%s' '$B64' | base64 -d > social-data/x_candidates.json
chown -R $VM_USER:$VM_USER social-data
echo "x_candidates.json uploaded (\$(wc -c < social-data/x_candidates.json) bytes)."
EOF
)
echo "Uploading $FILE to $VM ($RG) ..."
_run "$REMOTE"
echo "Done. The next scheduled collect will curate these X posts."
