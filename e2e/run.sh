#!/usr/bin/env bash
# Run the WC26 Intelligence e2e suite against a running stack.
#
#   1. Bring the stack up:   docker compose up -d --build   (frontend on :3000)
#   2. ./e2e/run.sh
#
# Seeds the deterministic finished fixture (app.data.seed_e2e_fixture) into the
# DB, then runs the Robot Framework suites. Override BASE_URL / DATABASE_URL as
# needed.
set -euo pipefail
cd "$(dirname "$0")"

: "${BASE_URL:=http://localhost:3000}"
: "${DATABASE_URL:=postgresql+psycopg://wc:wc@localhost:5432/worldcup}"

echo "› Seeding e2e fixture into ${DATABASE_URL%%\?*}"
( cd ../backend && DATABASE_URL="$DATABASE_URL" uv run python -m app.data.seed_e2e_fixture )

echo "› Running Robot suites against ${BASE_URL}"
robot --variable BASE_URL:"${BASE_URL}" --outputdir results suites/
