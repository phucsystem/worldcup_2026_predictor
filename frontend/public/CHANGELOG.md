# Changelog

What's shipping on the World Cup 2026 Intelligence platform. Newest first.

## v0.7.1 — 22 Jun 2026

- **Fixed** — Goalscorer data tests aligned with the new per-goal detail, restoring a green build on main.

## v0.7.0 — 22 Jun 2026

- **Added** — Goalscorers cards on match pages: colored team-initial avatars, inline flags, and goal minutes with penalty/own-goal detail and assists.
- **Improved** — Latest Results now highlights the winner (green score) and dims the losing side for at-a-glance reading.
- **Fixed** — Match hero flag backdrop no longer renders as solid blocks behind the banner.

## v0.6.0 — 21 Jun 2026

- **Added** — Official Buy Me a Coffee button in the header for visitors who want to back the project.

## v0.5.0 — 21 Jun 2026

- **Added** — Logs console: operators can inspect persisted line-level app logs from the dashboard.
- **Improved** — Latest Results now defaults to a date timeline, highlights match dates, and keeps grouped results ordered newest first.
- **Improved** — Main-branch PRs now require this changelog to be updated before merge.

## v0.4.0 — 19 Jun 2026

- **Added** — Fixtures page: upcoming matches by day with kickoff times in Australia/Melbourne, plus a projected knockout bracket (Round of 16 → Final).
- **Added** — Top scorers ("Stars to watch") and national team crests across standings and fixtures.
- **Added** — This changelog — a public progress log so anyone can follow what's shipping.
- **Improved** — Top navigation now scrolls cleanly on mobile as new sections are added.

## v0.3.0 — 18 Jun 2026

- **Added** — Next.js SSR site: daily brief list, brief detail, standings tables, and archive are live.
- **Improved** — Dark sports-dashboard design system applied across all screens (FIFA navy + electric blue).
- **Fixed** — Standings columns now use tabular figures so numbers align across every group.

## v0.2.0 — 17 Jun 2026

- **Added** — Automated daily publishing: Azure Container Apps Job runs the pipeline on a 7:00 AM AEST cron, no manual step.
- **Added** — Run logging in `agent_runs`: per-node timings, token counts, cost, and errors.
- **Improved** — Re-runs are now idempotent — re-triggering a day never duplicates a brief.

## v0.1.0 — 16 Jun 2026

- **Milestone** — First end-to-end brief generated and stored in the database — the full chain works.
- **Added** — LangGraph pipeline: Collector → Analyst → Editor. The LLM narrates only; it never does table math.
- **Added** — Deterministic standings math computed in Python (points, goal difference, position deltas, qualification).
- **Fixed** — Daylight-saving handling for the 7:00 AM Australia/Melbourne schedule.

## On the roadmap

- Premium model path (GPT-5 / Claude) behind the same provider interface.
- Prediction agent — projected qualification odds per group.
- Match-level fixture detail with key events.
