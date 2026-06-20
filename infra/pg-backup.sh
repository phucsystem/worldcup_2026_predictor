#!/usr/bin/env bash
# Phase 6 — light backup. Dumps Postgres from the running container and keeps the
# last 7 dumps. Data is regenerable (D2), so this is convenience, not DR.
# Install on the VM via cron, e.g. (daily 03:30):
#   30 3 * * * /home/azureuser/worldcup_2026_predictor/infra/pg-backup.sh >> /var/log/pg-backup.log 2>&1
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/pg-backups}"
KEEP="${KEEP:-7}"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U wc worldcup | gzip > "$BACKUP_DIR/worldcup-$STAMP.sql.gz"

ls -1t "$BACKUP_DIR"/worldcup-*.sql.gz | tail -n +$((KEEP + 1)) | xargs -r rm -f
echo "backup ok: $BACKUP_DIR/worldcup-$STAMP.sql.gz"
