#!/usr/bin/env bash
# Phase 5 — one manual pipeline run to seed data after first deploy.
# Run from the repo dir on the VM. Pass a date to backfill a specific day:
#   ./infra/seed.sh            # today
#   ./infra/seed.sh 2026-06-21 # specific date
set -euo pipefail

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)

if [[ -n "${1:-}" ]]; then
  "${COMPOSE[@]}" exec -T backend python -m app.pipeline.run --date "$1"
else
  "${COMPOSE[@]}" exec -T backend python -m app.pipeline.run
fi
echo ">> Seed run complete. Check the site, then confirm the scheduler refresh."
