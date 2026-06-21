---
title: Live In-Progress Match Detail Enhancements
description: ''
status: pending
priority: P2
branch: feat/live-match-events-update
tags: []
blockedBy: []
blocks: []
created: '2026-06-21T23:30:14.202Z'
createdBy: 'ck:plan'
source: skill
---

# Live In-Progress Match Detail Enhancements

## Overview

Enrich the live in-progress match page with detail the poll already carries (or can cheaply carry). The live data flow is already built end-to-end; this is mostly frontend rendering plus one backend addition (live statistics). Latency stays as-is (~120s backend poll + 30s frontend poll). Source: [`../reports/260622-live-match-detail-enhancements-brainstorm.md`](../reports/260622-live-match-detail-enhancements-brainstorm.md).

**Mode:** TDD — pure logic and the backend stats path are tested before implementation.

Scope items: **A** assists on timeline goals · **B** substitutions in↔out · **C** VAR rows · **D** penalty/own-goal markers in banner strip · **E** "just scored" live highlight · **F** live match statistics panel.

Out of scope: player photos (events carry no photo URL), tournament top-scorers leaderboard, latency/push-transport changes.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Timeline & Scorer Detail (A–D)](./phase-01-timeline-scorer-detail-a-d.md) | Completed |
| 2 | [Live Just-Scored Highlight (E)](./phase-02-live-just-scored-highlight-e.md) | Pending |
| 3 | [Live Match Statistics (F)](./phase-03-live-match-statistics-f.md) | Completed |

Phases are independent and individually shippable. Phase 1 is the natural first (most surface area). No hard ordering between 2 and 3.

## Acceptance criteria (whole plan)

- Timeline shows the assister on goals (A), both players on subs (B), and a distinct VAR row (C).
- Banner strip distinguishes penalty / own-goal from open-play goals (D).
- A goal/event arriving on a live poll is briefly highlighted; nothing flashes on initial SSR load (E).
- During an in-play match a live stats panel (possession/shots/xG/corners) appears and refreshes on the poll; a stats-fetch failure never breaks score/status updates (F).
- New/extended pure logic in `lib/match.ts` is covered by `lib/match.test.ts`; the `collect_live` stats path is covered in `backend/tests`.
- Existing Robot Framework e2e for the match page stays green.

## Dependencies

None. Overlapping plans (`260622-0438-match-final-stats-verdict`, `260621-1630-match-analysis-page`, `260621-0327-home-inprogress-live`) are all completed — this plan reuses their `MatchStats` component, `normalize_statistics`, and `FixtureDetail.statistics` rather than blocking on them.
