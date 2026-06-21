# End-to-end tests (Robot Framework)

Browser e2e for the WC26 Intelligence dashboard, using
[Robot Framework](https://robotframework.org/) + the
[Browser library](https://robotframework-browser.org/) (Playwright under the hood).

## What's covered

| Suite | Verifies |
|-------|----------|
| `suites/01_finished_match.robot` | **New feature** — finished match page shows the verdict, match-stats bars (incl. xG), key moments, goalscorers, and a verdict-model provenance credit. |
| `suites/02_results_navigation.robot` | **Bug fix** — a "Latest Results" row opens `/match/{id}` (not `/brief/{date}`) and renders the final-score hero. |
| `suites/03_regression_pages.robot` | **Regression** — home, standings, fixtures, changelog, and the match route all still render. |

Tests run against a deterministic finished fixture inserted by
`backend/app/data/seed_e2e_fixture.py` (no API-Football / LLM access needed), so
results are stable in CI.

## Run locally

```bash
# 1. Bring the stack up (frontend on :3000, backend + postgres)
docker compose up -d --build

# 2. Install the e2e deps (once)
python -m venv e2e/.venv && source e2e/.venv/bin/activate
pip install -r e2e/requirements.txt
rfbrowser init            # downloads the Playwright browser (once)

# 3. Seed + run
./e2e/run.sh              # or: HEADLESS=False ./e2e/run.sh to watch
```

Reports land in `e2e/results/` (`report.html`, `log.html`).

## CI

The `e2e` job in `.github/workflows/deploy.yml` runs the suite on every PR and
push to `main`: it starts Postgres, migrates, seeds the skeleton + the e2e
fixture, starts the backend and a production frontend build, then runs the
suites and uploads the Robot report as an artifact.

## Conventions

- Selectors prefer stable classes/ids already in the app (`.analysis-note`,
  `.stat-bars .sb-row`, `.results-widget .match-row`, `.next-match.is-final`).
- `${FIXTURE_ID}` (default `990001`) is the seeded finished match; override via
  `--variable FIXTURE_ID:<id>` to point at another match.
