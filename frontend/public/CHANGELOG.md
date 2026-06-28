# Changelog

What's shipping on the World Cup 2026 Intelligence platform. Newest first, grouped by release date.

## 29 Jun 2026

- **New** — The Knockout bracket now **highlights each winner's path** — the connector lines light up as ties finish, tracing every advancing team's route toward the Final.
- **Changed** — Renamed the **Fixtures** tab to **Matches**.
- **Changed** — Streamlined the top navigation: **Knockout** now takes the primary slot and the standalone Standings page is retired from the menu. Group standings still appear on the home page and on each match page.
- **New** — A dedicated **Knockout** page in the top navigation shows the full Round of 32 → Final bracket as a connected tree. Every round is visible from the start — later rounds shown as placeholders — and winners advance into the next round automatically as each game finishes, so you can follow the path to the Final end to end. The bracket is no longer duplicated inside Standings and Fixtures.

## 28 Jun 2026

- **Fixed** — Finished matches now switch from "live" to the final result on their own within a couple of minutes, instead of staying stuck on "live" until the next daily refresh.
- **Improved** — The "Forecast vs Reality" section now shows richer detail on both sides: the Forecast column adds pre-match key signals (FIFA rank, recent form, goals per game) and the Reality column shows an AI live read plus live match stats (possession, shots, xG) — both columns equal weight and bottom-aligned.
- **New** — Live match pages now show a "Forecast vs Reality" section comparing the pre-kickoff prediction to the actual scoreline as the game unfolds — with a live verdict (On track, Tighter than forecast, or Upset in progress) that updates as goals go in.
- **New** — Match forecasts now cover the knockout rounds too, not just the group stage — so every upcoming game (Round of 32 onward) gets a win/draw/win prediction with reasoning.
- **Improved** — Forecasts now weigh far more than the league table: world ranking, scoring rate, recent form, key absences (injuries/suspensions), and standout players — including famous names who haven't scored yet — for sharper, better-reasoned predictions.
- **Improved** — Forecasts no longer shy away from calling draws when teams are evenly matched, fixing a bias that previously missed too many drawn games.
- **Improved** — Forecasts for upcoming games can now be refreshed on demand, so prediction changes show up without waiting for the next daily update.
- **Docs** — Added an engineering write-up of the forecast algorithm (inputs, signals, prompts, and accuracy measurement) for contributors.
- **Changed** — The home "Up next" strip now shows every game from today's matchday (or the next match day, if today has none) instead of spilling the next two days together — so "today's games" means exactly that.
- **Fixed** — An open home page now switches a match from "Up next" to the live view on its own the moment it kicks off, instead of leaving a started game shown as upcoming with a stuck countdown until you reload.

## 26 Jun 2026

- **Fixed** — The live win-probability and AI "Live read" now actually reach production: the live-score service wasn't being updated on deploy (so it ran old code), and it lacked the key the AI read needs. Both are corrected, so in-play insights show and keep refreshing.
- **Improved** — The supporter feedback chat now opens itself once, a moment after your first page finishes loading, so it's easy to find and share a thought — then stays out of the way on later visits.
- **Fixed** — Live match pages now reliably show the live win-probability and the AI "Live read." A routine score refresh during a match was wiping each in-play game's group, which silently switched those live insights off mid-match; the group is now preserved so they keep updating to full time.

## 25 Jun 2026

- **Added** — The upcoming-match discussion panel now blends in **news reporting** alongside fan posts and is retitled "What people are saying." News headlines come from RSS/Atom feeds listed in an editable config file, are matched to the two teams, and pass through the same AI relevance + safety curation as the social posts (with a link back to each source). The forecast is still untouched — opinion and reporting never feed the model.
- **Added** — The match-page "Team status" panel now highlights each flagged player's reason at a glance: a red-card or second-yellow ban, a single yellow (one booking away), and — new — who's injured or doubtful, with the specific knock (e.g. "Calf Injury") shown. Injuries come straight from the official feed; suspensions already counted from cards are never double-listed.
- **Fixed** — The home "Upcoming" strip no longer truncates team names (e.g. "Türkiye vs USA" was clipping to "Tür"); cards now size to their content, wrap cleanly, and sit centered.
- **Improved** — Sharing any page now produces a proper link preview (title, description, and image) on social and chat, and the site is far easier for search engines to find: every section and match page has a unique, descriptive title, plus a sitemap and robots file so pages get discovered and indexed.
- **Added** — Live match pages now carry an AI "Live read" — a short, present-tense take on the game that refreshes after each goal, red card, or half — plus a live win-probability that shifts with the clock. The number is a calibrated Python model (score + time remaining) sharpened by a bounded AI adjustment for live context (xG, momentum, red cards), so it stays sane and updates every poll.
- **Added** — A win-probability comparison (before kickoff → now) and a swing chart that plots how the home side's chances have moved across the match, annotated with the goals. Without the AI key the win-probability still renders from the Python model alone.
- **Added** — When several matches are live at the same time (like the simultaneous final group-stage kickoffs), the home page now shows them all together in a side-by-side live board — each card with its live score, match clock, and what's at stake. A single live match keeps the larger spotlight banner.
- **Improved** — The home "Up next" strip now lists every upcoming game across the next two match days (up to six) instead of only the next two, so a busy day's fixtures are all visible at a glance.
- **Internal** — Added an `infra/set-admin-password.sh` helper to set the production admin password directly on the VM via Azure CLI (no SSH), prompting for the value so it never lands in shell history or logs.

## 24 Jun 2026

- **Added** — A "What fans are saying" panel on upcoming match pages: highlights of public fan discussion from Reddit and Bluesky, auto-curated for insight and shown alongside the forecast (with a link back to each source). The forecast itself is unchanged — fan opinion never feeds the model.
- **Improved** — The match hero banner now looks and behaves consistently across preview, live, and finished pages: the leading team is highlighted during a live match and after full time, with win/loss tags shown only once the result is final.
- **Added** — Upcoming match heroes (home and match pages) now show a glanceable win-probability bar, and sharing an upcoming match copies a forecast image — matchup, probability split, and kickoff — instead of a blank 0–0 scoreline.
- **Improved** — The home "Latest Results" section now shows every match from the last three result days instead of just the most recent eight, so a busy match day is never cut off.
- **Internal** — The deploy now syncs the admin password from the CI secret into the VM environment on each release, so it no longer has to be set on the server by hand.
- **Changed** — Admin sign-in now needs only the admin password; the separate session secret is gone. Existing admin sessions will need to sign in once more.
- **Fixed** — Own goals now show on the correct side of the match timeline, so the running score matches the final result (e.g. a 5–0 win no longer reads 4–1).
- **Added** — Finished match pages now have a "Watch highlights on SBS" link, matching the live "Watch on SBS" button.
- **Added** — A "Share result" button on finished and live match pages: it copies a branded scoreline image to your clipboard so you can paste it straight to a friend (with a share sheet on mobile and a download fallback).
- **Added** — Pasting a match link into a chat now shows a rich preview card with the scoreline banner.
- **Added** — A full results page listing every match from the start of the tournament, grouped by date. Reach it from the "View all results →" link in the home Latest Results section.
- **Added** — A friendly feedback chat in the bottom-right of every page: three host-nation supporters collect your bug reports and ideas in a couple of taps — no account needed.
- **Added** — A private admin area to review that feedback and mark each item done or won't-do.
- **Changed** — The system logs console moved into the admin area and is no longer public.
- **Added** — Upcoming and live match pages now show a "Team status" section: what each team needs from the game (must win, win or draw to stay top, already through, or eliminated).
- **Added** — Team status also lists players suspended for the match or one booking away from a ban, worked out from real card history, with key players starred.
- **Added** — Each date in "Latest Results" now shows how well the model's pre-match forecasts did that day (e.g. 3/4 · 75%), colored by accuracy.
- **Added** — Hover or tap a date's forecast rate to see the per-match breakdown — which results the model called and which it missed.
- **Improved** — Daily brief pages now open with a cinematic stadium hero and a cleaner reading layout.

## 23 Jun 2026

- **Fixed** — A missed penalty no longer counts as a goal, so the scoreline and goalscorers stay consistent (e.g. a 2–0 match no longer shows a hat-trick).
- **Added** — The live "Watch on SBS" button now opens an SBS On Demand search for the specific match instead of the generic football page.
- **Fixed** — The "Next 2" upcoming-fixture cards on the home page now open each match's analysis page instead of the full fixtures list.

## 22 Jun 2026

- **Added** — Match pages now show a pre-kickoff win-probability forecast — the win/draw/win split plus the factors driving it — generated by the model from each team's standings, replacing the earlier illustrative placeholder.
- **Fixed** — The header no longer overflows on small phones: the navigation links and Buy Me a Coffee button now stay within the screen.
- **Fixed** — Forecast factor labels no longer overlap the reasoning text on wider screens.
- **Added** — Live match pages now show live statistics (possession, shots, shots on target, xG, corners) that refresh while the match is in play.
- **Added** — A newly arrived goal, card, substitution, or VAR decision briefly highlights on the live timeline so you can spot what just happened.
- **Improved** — The Key moments timeline now shows the assister on goals, both players on substitutions (on ↔ off), and a dedicated row for VAR decisions.
- **Improved** — The live scoreline strip now marks penalties and own goals instead of showing every goal the same.
- **Added** — Completed match pages now show full match statistics (possession, shots, shots on target, xG, corners) from official data.
- **Added** — A one-line match verdict on completed matches — a neutral recap of the result, scorers, and group impact, narrated only from real data.
- **Fixed** — "Latest Results" rows now open the match page (score, stats, verdict, timeline) instead of the day's brief.
- **Fixed** — Local Docker dev now hot-reloads: frontend edits recompile live without a container restart.
- **Added** — Goalscorers cards on match pages: colored team-initial avatars, inline flags, and goal minutes with penalty/own-goal detail and assists.
- **Improved** — Latest Results now highlights the winner (green score) and dims the losing side for at-a-glance reading.
- **Fixed** — Match hero flag backdrop no longer renders as solid blocks behind the banner.
- **Internal** — Added a Robot Framework end-to-end suite (finished match page, results navigation, page regression), run on every PR in CI.
- **Fixed** — Goalscorer data tests aligned with the new per-goal detail, restoring a green build on main.

## 21 Jun 2026

- **Added** — Official Buy Me a Coffee button in the header for visitors who want to back the project.
- **Added** — Logs console: operators can inspect persisted line-level app logs from the dashboard.
- **Improved** — Latest Results now defaults to a date timeline, highlights match dates, and keeps grouped results ordered newest first.
- **Improved** — Main-branch PRs now require this changelog to be updated before merge.

## 19 Jun 2026

- **Added** — Fixtures page: upcoming matches by day with kickoff times in Australia/Melbourne, plus a projected knockout bracket (Round of 16 → Final).
- **Added** — Top scorers ("Stars to watch") and national team crests across standings and fixtures.
- **Added** — This changelog — a public progress log so anyone can follow what's shipping.
- **Improved** — Top navigation now scrolls cleanly on mobile as new sections are added.

## 18 Jun 2026

- **Added** — Next.js SSR site: daily brief list, brief detail, standings tables, and archive are live.
- **Improved** — Dark sports-dashboard design system applied across all screens (FIFA navy + electric blue).
- **Fixed** — Standings columns now use tabular figures so numbers align across every group.

## 17 Jun 2026

- **Added** — Automated daily publishing: Azure Container Apps Job runs the pipeline on a 7:00 AM AEST cron, no manual step.
- **Added** — Run logging in `agent_runs`: per-node timings, token counts, cost, and errors.
- **Improved** — Re-runs are now idempotent — re-triggering a day never duplicates a brief.

## 16 Jun 2026

- **Milestone** — First end-to-end brief generated and stored in the database — the full chain works.
- **Added** — LangGraph pipeline: Collector → Analyst → Editor. The LLM narrates only; it never does table math.
- **Added** — Deterministic standings math computed in Python (points, goal difference, position deltas, qualification).
- **Fixed** — Daylight-saving handling for the 7:00 AM Australia/Melbourne schedule.

## On the roadmap

- Premium model path (GPT-5 / Claude) behind the same provider interface.
- Prediction agent — projected qualification odds per group.
- Match-level fixture detail with key events.
