"""Unit tests for collect_live's live statistics + events fetch — no DB, no network.

collect_live talks to the DB via `upsert_matches` and a session factory; both are
faked here so the test isolates the per-fixture fetch behaviour (events + the
Phase F live statistics) without a Postgres dependency.
"""

import pytest

from app.data import collect


class FakeMatch:
    def __init__(self, fixture_id):
        self.fixture_id = fixture_id
        self.events = None
        self.statistics = None


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeSession:
    """Stands in for a SQLAlchemy session context manager. `execute(...).all()`
    returns the known fixture-id rows collect_live intersects live results with."""

    def __init__(self, known_ids):
        self._known = known_ids

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, _stmt):
        return FakeResult([(fid,) for fid in self._known])


def _factory(known_ids):
    return lambda: FakeSession(known_ids)


class FakeClient:
    def __init__(self, live, events=None, stats=None, stats_exc=False):
        self._live = live
        self._events = events if events is not None else [{"type": "Goal"}]
        self._stats = stats if stats is not None else [{"team": {"name": "France"}}]
        self._stats_exc = stats_exc
        self.events_calls = []
        self.stats_calls = []

    def get_fixtures(self, live=False):
        return self._live

    def get_events(self, fixture_id):
        self.events_calls.append(fixture_id)
        return self._events

    def get_fixture_statistics(self, fixture_id):
        self.stats_calls.append(fixture_id)
        if self._stats_exc:
            raise RuntimeError("stats boom")
        return self._stats


@pytest.fixture
def captured_upsert(monkeypatch):
    captured = {}

    def fake_upsert(_session, matches):
        captured["rows"] = list(matches)

    monkeypatch.setattr(collect, "upsert_matches", fake_upsert)
    return captured


class TestCollectLiveStatistics:
    def test_stores_statistics_for_in_play_fixture(self, captured_upsert):
        client = FakeClient(live=[FakeMatch(101)], stats=[{"team": {"name": "France"}}])
        n = collect.collect_live(_factory({101}), client)
        assert n == 1
        assert client.stats_calls == [101]
        assert captured_upsert["rows"][0].statistics == [{"team": {"name": "France"}}]

    def test_refetches_each_poll_no_once_only_guard(self, captured_upsert):
        client = FakeClient(live=[FakeMatch(101)])
        collect.collect_live(_factory({101}), client)
        collect.collect_live(_factory({101}), client)
        # called on every poll (live stats are overwritten, never skipped)
        assert client.stats_calls == [101, 101]

    def test_stats_failure_does_not_block_score_events_upsert(self, captured_upsert):
        m = FakeMatch(101)
        client = FakeClient(live=[m], stats_exc=True)
        n = collect.collect_live(_factory({101}), client)
        assert n == 1  # the score/status/events upsert still ran
        assert captured_upsert["rows"][0].fixture_id == 101
        assert m.statistics is None  # failed stats fetch left unset
        assert client.events_calls == [101]  # events still fetched

    def test_unknown_fixture_is_ignored(self, captured_upsert):
        client = FakeClient(live=[FakeMatch(999)])
        n = collect.collect_live(_factory({101}), client)
        assert n == 0
        assert client.stats_calls == []
        assert "rows" not in captured_upsert  # upsert never called
