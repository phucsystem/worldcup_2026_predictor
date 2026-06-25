"""Unit tests for the pure team-status logic (objective + suspensions). No I/O.

The accumulation ban-then-reset case is the crux: a player who served a ban must
never appear suspended two matches running for the same accumulation.
"""

from app.data.availability import (
    build_injured,
    build_team_status,
    compute_match_objective,
    compute_suspensions,
    last_match_contributors,
)
from app.data.models import StandingRow


def _injury(team, player, reason, type_="Missing Fixture"):
    return {"team": team, "player": player, "reason": reason, "type": type_}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _full_group(group_name, teams_pts):
    """teams_pts: [(team, points, gd, gf)] best-first, all played=3."""
    rows = []
    for i, (team, pts, gd, gf) in enumerate(teams_pts, start=1):
        rows.append(StandingRow(
            group_name=group_name, team=team,
            played=3, points=pts, gd=gd, gf=gf, position=i,
            won=pts // 3, drawn=pts % 3, lost=3 - (pts // 3) - (pts % 3),
            ga=gf - gd,
        ))
    return rows


def _incomplete_group(group_name, teams):
    """teams: [(team, played, points, gd, gf)] best-first."""
    rows = []
    for i, (team, played, pts, gd, gf) in enumerate(teams, start=1):
        rows.append(StandingRow(
            group_name=group_name, team=team,
            played=played, points=pts, gd=gd, gf=gf, position=i, ga=gf - gd,
        ))
    return rows


def _12_complete_groups():
    tables = {}
    for letter in "ABCDEFGHIJKL":
        gname = f"Group {letter}"
        tables[gname] = _full_group(gname, [
            (f"{letter}1", 9, 6, 7), (f"{letter}2", 6, 2, 4),
            (f"{letter}3", 3, -1, 2), (f"{letter}4", 0, -7, 0),
        ])
    return tables


def _card(team, player, detail):
    return {
        "type": "Card",
        "detail": detail,
        "team": {"name": team},
        "player": {"name": player},
    }


def _goal(team, player, assist=None):
    return {
        "type": "Goal",
        "detail": "Normal Goal",
        "team": {"name": team},
        "player": {"name": player},
        "assist": {"name": assist},
    }


def _match(events):
    return {"events_json": events}


# ---------------------------------------------------------------------------
# compute_match_objective
# ---------------------------------------------------------------------------

class TestObjective:
    def test_already_through(self):
        line, css = compute_match_objective(_12_complete_groups(), "A1")
        assert css == "qualified"
        assert "through" in line.lower()

    def test_eliminated(self):
        line, css = compute_match_objective(_12_complete_groups(), "A4")
        assert css == "out"
        assert "eliminated" in line.lower()

    def test_draw_enough_top_two(self):
        tables = {"Group A": _incomplete_group("Group A", [
            ("A1", 1, 3, 1, 2), ("A2", 1, 3, 1, 2),
            ("A3", 1, 0, -1, 0), ("A4", 1, 0, -1, 0),
        ])}
        line, css = compute_match_objective(tables, "A1")
        assert css == "contention"
        assert line == "Win or draw to stay top"

    def test_must_win_chaser(self):
        tables = {"Group A": _incomplete_group("Group A", [
            ("A1", 1, 3, 1, 2), ("A2", 1, 3, 1, 2),
            ("A3", 1, 0, -1, 0), ("A4", 1, 0, -1, 0),
        ])}
        line, css = compute_match_objective(tables, "A3")
        assert css == "contention"
        assert line == "Must win to advance"

    def test_empty_tables_omits_objective(self):
        assert compute_match_objective({}, "A1") == ("", "")

    def test_unknown_team_omits_objective(self):
        assert compute_match_objective(_12_complete_groups(), "Nowhere") == ("", "")


# ---------------------------------------------------------------------------
# compute_suspensions
# ---------------------------------------------------------------------------

class TestSuspensions:
    def test_clean_player_not_flagged(self):
        matches = [_match([_card("X", "Other", "Yellow Card")])]
        assert compute_suspensions(matches, "Brazil", key_names=set()) == []

    def test_single_yellow_is_at_risk(self):
        matches = [_match([_card("Brazil", "Neymar", "Yellow Card")])]
        out = compute_suspensions(matches, "Brazil", key_names=set())
        assert len(out) == 1
        assert out[0].player == "Neymar"
        assert out[0].status == "at_risk"
        assert out[0].reason == "one-yellow"

    def test_two_yellows_suspended_then_not_reflagged(self):
        # Yellow in M1 and M2 → ban served in M3 (this fixture) when M2 is latest.
        m1 = _match([_card("Brazil", "Casemiro", "Yellow Card")])
        m2 = _match([_card("Brazil", "Casemiro", "Yellow Card")])
        out = compute_suspensions([m1, m2], "Brazil", key_names=set())
        assert len(out) == 1
        assert out[0].status == "suspended"
        assert out[0].reason == "yellow-accumulation"

        # Once the ban is served (M3 played, clean), viewing M4 → not flagged.
        m3 = _match([])
        assert compute_suspensions([m1, m2, m3], "Brazil", key_names=set()) == []

    def test_red_card_suspends_next_match_only(self):
        m1 = _match([_card("Brazil", "Vinicius", "Red Card")])
        out = compute_suspensions([m1], "Brazil", key_names=set())
        assert len(out) == 1
        assert out[0].status == "suspended"
        assert out[0].reason == "red-card"

        # Served the following match → no longer flagged.
        m2 = _match([])
        assert compute_suspensions([m1, m2], "Brazil", key_names=set()) == []

    def test_second_yellow_is_direct_ban_not_double_counted(self):
        # One single yellow in M1, then a "Second Yellow card" in M2 (latest):
        # the second-yellow is a direct ban and must NOT push accumulation to 2.
        m1 = _match([_card("Brazil", "Rodrygo", "Yellow Card")])
        m2 = _match([_card("Brazil", "Rodrygo", "Second Yellow card")])
        out = compute_suspensions([m1, m2], "Brazil", key_names=set())
        assert len(out) == 1
        assert out[0].status == "suspended"
        assert out[0].reason == "red-card"  # direct ban, not "yellow-accumulation"

    def test_key_player_flag(self):
        matches = [_match([_card("Brazil", "Neymar", "Yellow Card")])]
        out = compute_suspensions(matches, "Brazil", key_names={"Neymar"})
        assert out[0].key_player is True


# ---------------------------------------------------------------------------
# last_match_contributors
# ---------------------------------------------------------------------------

class TestContributors:
    def test_scorer_and_assister_collected(self):
        m = _match([_goal("Brazil", "Neymar", assist="Raphinha")])
        assert last_match_contributors([m], "Brazil") == {"Neymar", "Raphinha"}

    def test_only_latest_match_counts(self):
        old = _match([_goal("Brazil", "Old Player")])
        latest = _match([_goal("Brazil", "Neymar")])
        assert last_match_contributors([old, latest], "Brazil") == {"Neymar"}

    def test_empty_when_no_matches(self):
        assert last_match_contributors([], "Brazil") == set()


# ---------------------------------------------------------------------------
# build_team_status
# ---------------------------------------------------------------------------

class TestBuildTeamStatus:
    def test_splits_suspended_and_at_risk(self):
        tables = _12_complete_groups()
        m1 = _match([
            _card("A1", "Banned Guy", "Red Card"),
            _card("A1", "Risky Guy", "Yellow Card"),
        ])
        status = build_team_status(tables, "A1", [m1], key_names=set())
        assert status is not None
        assert [p.player for p in status.unavailable] == ["Banned Guy"]
        assert [p.player for p in status.at_risk] == ["Risky Guy"]
        assert status.objective_css == "qualified"

    def test_none_when_nothing_to_show(self):
        # Unknown group (empty objective) + no card history → nothing to render.
        assert build_team_status({}, "Ghost", [], key_names=set()) is None

    def test_injuries_populate_injured_list(self):
        tables = _12_complete_groups()
        injuries = [
            _injury("A1", "Hurt Guy", "Calf Injury"),
            _injury("A1", "Maybe Guy", "Knock", type_="Questionable"),
            _injury("B1", "Other Team Guy", "Illness"),  # wrong team, ignored
        ]
        status = build_team_status(tables, "A1", [], key_names=set(), injury_records=injuries)
        assert [(p.player, p.status, p.reason) for p in status.injured] == [
            ("Hurt Guy", "injured", "Calf Injury"),
            ("Maybe Guy", "doubtful", "Knock"),
        ]

    def test_only_injuries_present_still_renders(self):
        # No objective, no cards — an injury alone is enough to render the panel.
        status = build_team_status({}, "Solo", [], key_names=set(),
                                   injury_records=[_injury("Solo", "Hurt", "Sprain")])
        assert status is not None
        assert [p.player for p in status.injured] == ["Hurt"]


class TestBuildInjured:
    def test_suspension_reasons_filtered_out(self):
        # The /injuries feed lists bans as missing-fixture rows; the card replay
        # already owns those, so they must not re-appear in the injured list.
        recs = [
            _injury("A1", "Banned Red", "Red Card"),
            _injury("A1", "Banned Yellow", "Yellow card suspension"),
            _injury("A1", "Genuinely Hurt", "Hamstring"),
        ]
        injured = build_injured(recs, "A1", key_names=set())
        assert [p.player for p in injured] == ["Genuinely Hurt"]

    def test_excludes_already_flagged_players(self):
        recs = [_injury("A1", "Double Listed", "Muscle bruise")]
        injured = build_injured(recs, "A1", key_names=set(), exclude={"Double Listed"})
        assert injured == []

    def test_dedupes_within_feed_and_marks_key_player(self):
        recs = [
            _injury("A1", "Star", "Knock"),
            _injury("A1", "Star", "Knock"),  # duplicate row
        ]
        injured = build_injured(recs, "A1", key_names={"Star"})
        assert len(injured) == 1
        assert injured[0].key_player is True
