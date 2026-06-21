"""Unit tests for /fixtures/statistics → MatchStat shaping — no DB, no network."""

from app.api.fixtures import MatchStat, normalize_statistics

HOME = "Brazil"
AWAY = "Serbia"


def _entry(team, **stats):
    # API-Football shape: {"team": {"name": ...}, "statistics": [{"type","value"}]}
    type_map = {
        "possession": "Ball Possession",
        "shots": "Total Shots",
        "sot": "Shots on Goal",
        "xg": "expected_goals",
        "corners": "Corner Kicks",
    }
    return {
        "team": {"name": team},
        "statistics": [{"type": type_map[k], "value": v} for k, v in stats.items()],
    }


def _raw_full():
    return [
        _entry(HOME, possession="58%", shots=18, sot=8, xg="2.90", corners=8),
        _entry(AWAY, possession="42%", shots=10, sot=3, xg="1.20", corners=4),
    ]


class TestNormalizeStatistics:
    def test_empty_and_none(self):
        assert normalize_statistics(None, HOME, AWAY) == []
        assert normalize_statistics([], HOME, AWAY) == []

    def test_order_matches_prototype(self):
        out = normalize_statistics(_raw_full(), HOME, AWAY)
        assert [s.label for s in out] == [
            "Possession", "Shots", "Shots on target", "Expected goals (xG)", "Corners",
        ]

    def test_possession_percentages(self):
        out = normalize_statistics(_raw_full(), HOME, AWAY)
        poss = out[0]
        assert poss.home == "58%" and poss.away == "42%"
        assert poss.home_pct == 58.0 and poss.away_pct == 42.0

    def test_count_percentages_sum_to_100(self):
        out = normalize_statistics(_raw_full(), HOME, AWAY)
        shots = next(s for s in out if s.label == "Shots")
        assert shots.home == "18" and shots.away == "10"
        assert round(shots.home_pct + shots.away_pct, 1) == 100.0
        assert shots.home_pct > shots.away_pct  # 18 vs 10

    def test_xg_float_percentages(self):
        out = normalize_statistics(_raw_full(), HOME, AWAY)
        xg = next(s for s in out if s.label == "Expected goals (xG)")
        assert xg.home == "2.90" and xg.away == "1.20"
        assert round(xg.home_pct + xg.away_pct, 1) == 100.0

    def test_missing_stat_type_is_omitted(self):
        raw = [
            _entry(HOME, possession="55%", shots=12),
            _entry(AWAY, possession="45%", shots=9),
        ]
        out = normalize_statistics(raw, HOME, AWAY)
        labels = [s.label for s in out]
        assert labels == ["Possession", "Shots"]  # no SoT/xG/corners in payload

    def test_zero_zero_does_not_crash(self):
        raw = [_entry(HOME, corners=0), _entry(AWAY, corners=0)]
        out = normalize_statistics(raw, HOME, AWAY)
        corners = out[0]
        assert corners.label == "Corners"
        assert corners.home_pct == 0.0 and corners.away_pct == 0.0

    def test_team_matching_is_by_name_not_order(self):
        # away listed first in payload — must still map by team name
        raw = [
            _entry(AWAY, possession="40%"),
            _entry(HOME, possession="60%"),
        ]
        out = normalize_statistics(raw, HOME, AWAY)
        assert out[0].home == "60%" and out[0].away == "40%"

    def test_returns_matchstat_instances(self):
        out = normalize_statistics(_raw_full(), HOME, AWAY)
        assert all(isinstance(s, MatchStat) for s in out)
