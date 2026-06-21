"""Unit tests for the verdict fact-bundle builder + backfill selection.

No DB, no network, no LLM — the builder is pure and is the ONLY thing handed to
DeepSeek, so it is the fabrication-guard that must be exercised directly.
"""

from app.api.fixtures import MatchEvent, select_fixtures_needing_verdict
from app.data.models import Match, StandingRow
from app.pipeline.verdict import build_match_verdict_facts

HOME = "Brazil"
AWAY = "Serbia"


def _goal(minute, side, player, detail="Normal Goal"):
    team = HOME if side == "home" else AWAY
    return MatchEvent(minute=minute, type="Goal", detail=detail, player=player, side=side, team=team)


def _rows():
    return [
        StandingRow(group_name="G", team="Brazil", points=9, position=1, qualification="qualified"),
        StandingRow(group_name="G", team="Serbia", points=3, position=3, qualification="contention"),
    ]


class TestBuildVerdictFacts:
    def _facts(self, hs, as_, events, rows=None):
        return build_match_verdict_facts(
            home_team=HOME, away_team=AWAY, home_score=hs, away_score=as_,
            events=events, group_name="G", group_rows=rows or _rows(),
        )

    def test_home_win_result_and_winner(self):
        f = self._facts(3, 1, [_goal(51, "home", "Vinícius Jr")])
        assert f["result"] == "home_win"
        assert f["winner"] == "Brazil"
        assert f["home_score"] == 3 and f["away_score"] == 1

    def test_away_win(self):
        f = self._facts(0, 2, [_goal(10, "away", "Mitrović")])
        assert f["result"] == "away_win"
        assert f["winner"] == "Serbia"

    def test_draw_has_no_winner(self):
        f = self._facts(1, 1, [_goal(20, "home", "A"), _goal(80, "away", "B")])
        assert f["result"] == "draw"
        assert f["winner"] is None

    def test_scorers_credited_to_scoring_side(self):
        f = self._facts(2, 0, [_goal(51, "home", "Vinícius Jr"), _goal(78, "home", "Rodrygo")])
        assert f["scorers"] == [
            {"player": "Vinícius Jr", "team": "Brazil", "minute": 51, "own_goal": False},
            {"player": "Rodrygo", "team": "Brazil", "minute": 78, "own_goal": False},
        ]

    def test_own_goal_credited_to_opponent(self):
        # An away player's own goal counts for the home team.
        f = self._facts(1, 0, [_goal(30, "away", "Defender", detail="Own Goal")])
        assert f["scorers"] == [
            {"player": "Defender", "team": "Brazil", "minute": 30, "own_goal": True},
        ]

    def test_non_goal_events_ignored(self):
        card = MatchEvent(minute=40, type="Card", detail="Yellow Card", player="X", side="home", team=HOME)
        f = self._facts(1, 0, [_goal(10, "home", "A"), card])
        assert len(f["scorers"]) == 1

    def test_no_events_means_no_scorers(self):
        f = self._facts(0, 0, [])
        assert f["scorers"] == []

    def test_group_standings_projected(self):
        f = self._facts(3, 1, [])
        assert f["group_name"] == "G"
        assert {"position": 1, "team": "Brazil", "points": 9, "qualification": "qualified"} in f["group_standings"]

    def test_no_group_rows_yields_empty_standings(self):
        f = build_match_verdict_facts(
            home_team=HOME, away_team=AWAY, home_score=1, away_score=0,
            events=[], group_name=None, group_rows=[],
        )
        assert f["group_standings"] == []


def _match(fid, status):
    return Match(
        fixture_id=fid, group_name=None, home_team=HOME, away_team=AWAY,
        home_score=None, away_score=None, status=status, kickoff_utc=None,
    )


class TestSelectFixturesNeedingVerdict:
    def test_finished_without_verdict_is_selected(self):
        assert select_fixtures_needing_verdict([_match(1, "FT")], existing=set()) == [1]

    def test_finished_with_verdict_is_skipped(self):
        assert select_fixtures_needing_verdict([_match(1, "FT")], existing={1}) == []

    def test_live_and_upcoming_skipped(self):
        assert select_fixtures_needing_verdict([_match(1, "2H"), _match(2, "NS")], existing=set()) == []
