"""Pure, deterministic team-status computation for the match page: a team's
match objective and player availability. No I/O — it accepts already-loaded rows,
mirroring `standings_math.py` — so it is unit-tested directly.

Objectives reuse the standings scenario vocabulary; suspensions are replayed
statefully from stored card events. No mood/fitness, no external API.
"""

from collections import defaultdict
from typing import Optional, Sequence

from app.data.models import PlayerStatus, StandingRow, TeamStatus
from app.data.standings_math import group_scenarios

# API-Football card details (events with type == "Card"). A red or a second
# yellow is a direct next-match ban; a single yellow feeds the accumulation
# counter (2 across matches → ban, then the counter resets).
_DIRECT_BAN_DETAILS = {"Red Card", "Second Yellow card"}
_YELLOW_DETAIL = "Yellow Card"
_YELLOW_BAN_THRESHOLD = 2


def compute_match_objective(
    all_group_tables: dict[str, list[StandingRow]], team: str
) -> tuple[str, str]:
    """(objective line, css token) describing what `team` needs from this fixture.

    Reuses `standings_math.group_scenarios` (locked decision: reuse the simplified
    through / out / win-or-draw / must-win vocabulary rather than fork true
    draw-sufficiency math). Returns ("", "") when the team is absent from the
    tables (knockout / unknown group) so the objective block can be omitted.
    """
    scenarios = group_scenarios(all_group_tables)
    for rows in scenarios.values():
        for r in rows:
            if r["team"] != team:
                continue
            css = r["status"]
            if css == "qualified":
                return ("Already through — playing for seeding", "qualified")
            if css == "out":
                return ("Eliminated — pride only", "out")
            if r["position"] in (1, 2):
                return ("Win or draw to stay top", "contention")
            return ("Must win to advance", "contention")
    return ("", "")


def _team_card_events(match: dict, team: str) -> list[dict]:
    return [
        ev
        for ev in (match.get("events_json") or [])
        if ev.get("type") == "Card" and (ev.get("team") or {}).get("name") == team
    ]


def compute_suspensions(
    team_matches_in_order: Sequence[dict], team: str, *, key_names: set[str]
) -> list[PlayerStatus]:
    """Replay `team`'s finished group matches (oldest→newest) and return who is
    suspended for, or one booking away from, the NEXT (this) fixture.

    Stateful rules (locked in plan Validation Session 1):
      - "Red Card" / "Second Yellow card" → direct one-match ban; does NOT feed
        the single-yellow accumulation counter.
      - "Yellow Card" → increment a per-player counter; on the 2nd a ban is
        incurred and the counter RESETS to 0, so a served ban never re-flags.
    A ban incurred in the LATEST match is served in this fixture (suspended). A
    player carrying exactly one single yellow after the latest match is at_risk.
    """
    single_yellows: dict[str, int] = defaultdict(int)
    suspended_reason: dict[str, str] = {}  # bans incurred in the latest match only
    last_index = len(team_matches_in_order) - 1

    for idx, match in enumerate(team_matches_in_order):
        for ev in _team_card_events(match, team):
            player = (ev.get("player") or {}).get("name")
            if not player:
                continue
            detail = ev.get("detail")
            if detail in _DIRECT_BAN_DETAILS:
                if idx == last_index:
                    suspended_reason[player] = "red-card"
            elif detail == _YELLOW_DETAIL:
                single_yellows[player] += 1
                if single_yellows[player] >= _YELLOW_BAN_THRESHOLD:
                    if idx == last_index:
                        suspended_reason[player] = "yellow-accumulation"
                    single_yellows[player] = 0

    statuses: list[PlayerStatus] = [
        PlayerStatus(
            player=player,
            reason=reason,
            status="suspended",
            key_player=player in key_names,
        )
        for player, reason in suspended_reason.items()
    ]
    for player, count in single_yellows.items():
        if count == 1 and player not in suspended_reason:
            statuses.append(
                PlayerStatus(
                    player=player,
                    reason="one-yellow",
                    status="at_risk",
                    key_player=player in key_names,
                )
            )
    return statuses


def build_injured(
    injury_records: Sequence[dict], team: str, *, key_names: set[str], exclude: set[str] = frozenset()
) -> list[PlayerStatus]:
    """`team`'s injured/doubtful players for this fixture from stored API-Football
    /injuries records. `type` "Missing Fixture" → ruled out (status "injured");
    anything else (e.g. "Questionable") → status "doubtful". `reason` carries the
    API reason text (e.g. "Calf Injury"). Records for the other side are ignored.

    The /injuries feed also lists SUSPENSIONS (reasons like "Red Card" or "Yellow
    card suspension") as missing-fixture rows; those are skipped here because the
    card-event replay already covers bans — surfacing them again would double-list
    the player. `exclude` drops anyone already flagged (suspended / at risk)."""
    statuses: list[PlayerStatus] = []
    seen: set[str] = set()
    for rec in injury_records or []:
        if (rec.get("team") or "") != team:
            continue
        player = rec.get("player")
        if not player or player in seen or player in exclude:
            continue
        reason = rec.get("reason") or ""
        low = reason.lower()
        if "card" in low or "suspen" in low:
            continue  # a ban, not an injury — owned by the card-replay logic
        seen.add(player)
        ruled_out = (rec.get("type") or "") == "Missing Fixture"
        statuses.append(
            PlayerStatus(
                player=player,
                reason=rec.get("reason") or ("Injured" if ruled_out else "Doubtful"),
                status="injured" if ruled_out else "doubtful",
                key_player=player in key_names,
            )
        )
    return statuses


def last_match_contributors(team_matches_in_order: Sequence[dict], team: str) -> set[str]:
    """Names who scored or assisted for `team` in their most recent finished
    match — used to emphasise key players. Own goals are excluded (the scorer
    plays for the other side). Empty when there are no prior matches."""
    if not team_matches_in_order:
        return set()
    names: set[str] = set()
    for ev in team_matches_in_order[-1].get("events_json") or []:
        if ev.get("type") != "Goal" or (ev.get("detail") or "") == "Own Goal":
            continue
        if (ev.get("team") or {}).get("name") != team:
            continue
        for who in (
            (ev.get("player") or {}).get("name"),
            (ev.get("assist") or {}).get("name"),
        ):
            if who:
                names.add(who)
    return names


def build_team_status(
    all_group_tables: dict[str, list[StandingRow]],
    team: str,
    team_matches_in_order: Sequence[dict],
    *,
    key_names: set[str],
    injury_records: Sequence[dict] = (),
) -> Optional[TeamStatus]:
    """Assemble a `TeamStatus` for one side, or None when there is nothing to
    show (no objective and no flagged players) — keeps the response clean."""
    objective, css = compute_match_objective(all_group_tables, team)
    players = compute_suspensions(team_matches_in_order, team, key_names=key_names)
    unavailable = [p for p in players if p.status == "suspended"]
    at_risk = [p for p in players if p.status == "at_risk"]
    flagged = {p.player for p in players}
    injured = build_injured(injury_records, team, key_names=key_names, exclude=flagged)
    if not objective and not unavailable and not at_risk and not injured:
        return None
    return TeamStatus(
        objective=objective,
        objective_css=css,
        unavailable=unavailable,
        at_risk=at_risk,
        injured=injured,
    )
