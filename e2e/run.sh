#!/usr/bin/env bash
# Run the WC26 Intelligence e2e suite against a running stack.
#
#   1. Bring the stack up:   docker compose up -d --build   (frontend on :3000)
#   2. ./e2e/run.sh
#
# Self-bootstrapping and shell-agnostic: creates ./.venv and installs deps on
# first run, then invokes the venv's own robot binary directly — no `source
# .venv/bin/activate` needed (so it works the same in bash, zsh, and fish).
# Seeds the deterministic finished fixture (app.data.seed_e2e_fixture) into the
# DB before running. Override BASE_URL / DATABASE_URL as needed.
set -euo pipefail
cd "$(dirname "$0")"

: "${BASE_URL:=http://localhost:3000}"
: "${DATABASE_URL:=postgresql+psycopg://wc:wc@localhost:5432/worldcup}"

VENV=".venv"
if [ ! -x "${VENV}/bin/robot" ]; then
  echo "› First run: creating ${VENV} and installing e2e deps"
  python3 -m venv "${VENV}"
  "${VENV}/bin/pip" install -q -r requirements.txt
  "${VENV}/bin/rfbrowser" init chromium
fi

echo "› Seeding e2e fixture into ${DATABASE_URL%%\?*}"
( cd ../backend && DATABASE_URL="$DATABASE_URL" uv run python -m app.data.seed_e2e_fixture )

echo "› Running Robot suites against ${BASE_URL}"
"${VENV}/bin/robot" --variable BASE_URL:"${BASE_URL}" --outputdir results suites/
