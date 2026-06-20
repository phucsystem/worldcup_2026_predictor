"""
Unit tests for the standings trend shaper in app.api.standings — no DB.
shape_trend orders snapshots oldest→newest and keeps the last `window`.
"""

from datetime import date

from app.api.standings import shape_trend


def _row(d, position, points):
    return {"snapshot_date": d, "position": position, "points": points}


class TestShapeTrend:
    def test_orders_oldest_to_newest(self):
        rows = [
            _row(date(2026, 6, 14), 2, 4),
            _row(date(2026, 6, 12), 3, 1),
            _row(date(2026, 6, 16), 1, 7),
        ]
        out = shape_trend(rows, window=5)
        assert [p.snapshot_date for p in out] == [
            date(2026, 6, 12), date(2026, 6, 14), date(2026, 6, 16)
        ]
        assert [p.points for p in out] == [1, 4, 7]

    def test_window_keeps_last_n(self):
        rows = [_row(date(2026, 6, d), d, d) for d in range(10, 18)]
        out = shape_trend(rows, window=3)
        assert len(out) == 3
        assert [p.snapshot_date.day for p in out] == [15, 16, 17]

    def test_window_larger_than_available_returns_all(self):
        rows = [_row(date(2026, 6, 12), 3, 1), _row(date(2026, 6, 14), 2, 4)]
        out = shape_trend(rows, window=5)
        assert len(out) == 2

    def test_no_snapshots_returns_empty(self):
        assert shape_trend([], window=5) == []
