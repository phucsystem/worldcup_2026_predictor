"""Unit tests for collect_live's live statistics + events fetch — no DB, no network.

collect_live talks to the DB via `upsert_matches` and a session factory; both are
faked here so the test isolates the per-fixture fetch behaviour (events + the
Phase F live statistics) without a Postgres dependency.
"""

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.data import collect
from app.data import repository as repo
from app.data.models import Match


class FakeMatch:
    def __init__(self, fixture_id, *, status="2H", home_team="France", away_team="Spain",
                 home_score=1, away_score=0, elapsed=60):
        self.fixture_id = fixture_id
        self.status = status
        self.home_team = home_team
        self.away_team = away_team
        self.home_score = home_score
        self.away_score = away_score
        self.elapsed = elapsed
        self.events = None
        self.statistics = None
        self.live_winprob_json = None
        self.live_winprob_adj_json = None
        self.live_winprob_history_json = None
        self.live_read_text = None
        self.live_read_model = None
        self.live_read_sig = None


class FakeMappings:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def mappings(self):
        return FakeMappings(self._rows)


class FakeSession:
    """Stands in for a SQLAlchemy session context manager. `execute(...).mappings()
    .all()` returns the stored fixture rows collect_live intersects live results
    with (a mapping per fixture carrying group_name + win-prob state)."""

    def __init__(self, stored_rows):
        self._rows = stored_rows

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, _stmt):
        return FakeResult(self._rows)


def _stored_row(fixture_id, *, group_name=None, forecast_json=None, adj=None,
                history=None, sig=None, status=None, kickoff_utc=None):
    return {
        "fixture_id": fixture_id,
        "group_name": group_name,
        "forecast_json": forecast_json,
        "live_winprob_adj_json": adj,
        "live_winprob_history_json": history,
        "live_read_sig": sig,
        "status": status,
        "kickoff_utc": kickoff_utc,
    }


def _factory(known_ids):
    """Stored rows for the given ids with no group_name (win-prob skipped) — keeps
    the statistics/events tests focused on the fetch behaviour."""
    rows = [_stored_row(fid) for fid in known_ids]
    return lambda: FakeSession(rows)


def _factory_rows(rows):
    return lambda: FakeSession(rows)


class FakeClient:
    def __init__(self, live, events=None, stats=None, stats_exc=False, full=None):
        self._live = live
        self._full = full  # returned when get_fixtures(live=False) is called
        self._events = events if events is not None else [{"type": "Goal"}]
        self._stats = stats if stats is not None else [{"team": {"name": "France"}}]
        self._stats_exc = stats_exc
        self.events_calls = []
        self.stats_calls = []
        self.full_fetch_calls = 0

    def get_fixtures(self, live=False):
        if live:
            return self._live
        self.full_fetch_calls += 1
        return self._full if self._full is not None else []

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


def _raw_goal(minute, team):
    return {"time": {"elapsed": minute}, "type": "Goal", "detail": "Normal Goal",
            "team": {"name": team}, "player": {"name": "X"}}


class TestCollectLiveWinProb:
    @pytest.fixture(autouse=True)
    def _no_llm(self, monkeypatch):
        # Phase 2 path is pure (no LLM): the agent only sets the adjustment, which
        # these tests exercise via a pre-stored adj, not a live agent call.
        monkeypatch.setattr(collect.settings, "DEEPSEEK_API_KEY", "")

    def test_group_stage_in_play_stores_base_with_no_adjustment(self, captured_upsert):
        from app.pipeline.winprob import apply_adjustment, compute_base

        m = FakeMatch(101, status="2H", home_team="France", away_team="Spain",
                      home_score=1, away_score=0, elapsed=60)
        client = FakeClient(live=[m], events=[_raw_goal(30, "France")], stats=None)
        rows = [_stored_row(101, group_name="A")]
        collect.collect_live(_factory_rows(rows), client)

        stored = captured_upsert["rows"][0]
        expected = apply_adjustment(compute_base(1, 0, 60, prior=None), None)
        assert stored.live_winprob_json == expected  # final == base (no stored adj, no LLM)
        # History seeded with a KO point and one event point.
        assert stored.live_winprob_history_json[0]["label"] == "KO"
        assert stored.live_winprob_history_json[-1]["label"] == "Goal · France"
        assert stored.live_winprob_history_json[-1]["minute"] == 60

    def test_knockout_match_skips_winprob(self, captured_upsert):
        m = FakeMatch(101, status="2H")
        client = FakeClient(live=[m], events=[_raw_goal(30, "France")])
        rows = [_stored_row(101, group_name=None)]  # knockout → no group
        collect.collect_live(_factory_rows(rows), client)
        assert captured_upsert["rows"][0].live_winprob_json is None

    def test_stored_adjustment_is_reapplied_each_poll(self, captured_upsert):
        from app.pipeline.winprob import apply_adjustment, compute_base

        m = FakeMatch(101, status="2H", home_score=1, away_score=0, elapsed=60)
        adj = {"home": 8, "draw": -4, "away": -4}
        client = FakeClient(live=[m], events=[_raw_goal(30, "France")])
        rows = [_stored_row(101, group_name="A", adj=adj)]
        collect.collect_live(_factory_rows(rows), client)

        expected = apply_adjustment(compute_base(1, 0, 60), adj)
        assert captured_upsert["rows"][0].live_winprob_json == expected

    def test_history_not_appended_when_signature_unchanged(self, captured_upsert):
        from app.pipeline.winprob import live_read_signature
        from app.api.fixtures import normalize_events

        events = [_raw_goal(30, "France")]
        norm = normalize_events(events, "France", "Spain")
        sig = live_read_signature(norm, "2H", 60)
        existing_history = [{"minute": 0, "home_score": 0, "away_score": 0,
                             "home_pct": 40, "draw_pct": 30, "away_pct": 30, "label": "KO"}]
        m = FakeMatch(101, status="2H", home_score=1, away_score=0, elapsed=60)
        client = FakeClient(live=[m], events=events)
        rows = [_stored_row(101, group_name="A", sig=sig, history=existing_history)]
        collect.collect_live(_factory_rows(rows), client)

        stored = captured_upsert["rows"][0]
        assert stored.live_winprob_json is not None       # win-prob still recomputed
        assert stored.live_winprob_history_json is None    # but history not touched


class TestCollectLiveAgentGating:
    """The agent runs only on a significant-event signature change, and only when
    DEEPSEEK_API_KEY is set. Gating lives in collect_live; the agent itself is faked."""

    @pytest.fixture
    def fake_agent(self, monkeypatch):
        calls = []

        def fake_run(_session, m, base, events, group_name, minute):
            calls.append(m.fixture_id)
            return ({"adjustment": {"home": 5, "draw": -2, "away": -3},
                     "read": "Live read."}, "deepseek-chat")

        monkeypatch.setattr(collect, "_run_live_agent", fake_run)
        monkeypatch.setattr(collect.settings, "DEEPSEEK_API_KEY", "test-key")
        return calls

    def test_agent_called_on_sig_change_and_writes_adj_and_read(self, captured_upsert, fake_agent):
        m = FakeMatch(101, status="2H", home_score=1, away_score=0, elapsed=60)
        client = FakeClient(live=[m], events=[_raw_goal(30, "France")])
        rows = [_stored_row(101, group_name="A", sig=None)]  # no stored sig → changed
        collect.collect_live(_factory_rows(rows), client)

        assert fake_agent == [101]
        stored = captured_upsert["rows"][0]
        assert stored.live_winprob_adj_json == {"home": 5, "draw": -2, "away": -3}
        assert stored.live_read_text == "Live read."
        assert stored.live_read_model == "deepseek-chat"
        assert stored.live_read_sig is not None

    def test_agent_not_called_when_signature_unchanged(self, captured_upsert, fake_agent):
        from app.api.fixtures import normalize_events
        from app.pipeline.winprob import live_read_signature

        events = [_raw_goal(30, "France")]
        sig = live_read_signature(normalize_events(events, "France", "Spain"), "2H", 60)
        m = FakeMatch(101, status="2H", home_score=1, away_score=0, elapsed=60)
        client = FakeClient(live=[m], events=events)
        rows = [_stored_row(101, group_name="A", sig=sig)]
        collect.collect_live(_factory_rows(rows), client)
        assert fake_agent == []  # signature unchanged → no agent call

    def test_agent_skipped_without_api_key(self, captured_upsert, monkeypatch):
        monkeypatch.setattr(collect.settings, "DEEPSEEK_API_KEY", "")
        ran = []
        monkeypatch.setattr(collect, "_run_live_agent", lambda *a: ran.append(1))
        m = FakeMatch(101, status="2H", home_score=1, away_score=0, elapsed=60)
        client = FakeClient(live=[m], events=[_raw_goal(30, "France")])
        rows = [_stored_row(101, group_name="A", sig=None)]
        collect.collect_live(_factory_rows(rows), client)
        assert ran == []  # no key → agent skipped, base still renders
        assert captured_upsert["rows"][0].live_winprob_json is not None


@pytest.fixture
def sqlite_session():
    engine = sa.create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    repo.matches_table.create(bind=engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


def _match(fixture_id, **kw):
    base = dict(
        fixture_id=fixture_id, group_name="A", home_team="France", away_team="Spain",
        home_score=1, away_score=0, status="2H", kickoff_utc=None,
    )
    base.update(kw)
    return Match(**base)


class TestUpsertLiveWinProbColumns:
    def test_winprob_and_read_round_trip(self, sqlite_session):
        repo.upsert_matches(sqlite_session, [_match(
            1,
            live_winprob_json={"home": 55, "draw": 25, "away": 20},
            live_winprob_adj_json={"home": 5, "draw": -2, "away": -3},
            live_winprob_history_json=[{"minute": 0, "label": "KO"}],
            live_read_text="France lead through an early goal.",
            live_read_model="deepseek-chat",
            live_read_sig="2H|goals=1|reds=0|bucket=4",
        )])
        row = sqlite_session.execute(
            sa.select(repo.matches_table).where(repo.matches_table.c.fixture_id == 1)
        ).mappings().first()
        assert row["live_winprob_json"] == {"home": 55, "draw": 25, "away": 20}
        assert row["live_read_text"] == "France lead through an early goal."
        assert row["live_read_sig"] == "2H|goals=1|reds=0|bucket=4"

    def test_winprob_overwrites_but_read_is_keep_last_good(self, sqlite_session):
        repo.upsert_matches(sqlite_session, [_match(
            1,
            live_winprob_json={"home": 55, "draw": 25, "away": 20},
            live_read_text="Early read.",
            live_read_model="deepseek-chat",
            live_read_sig="sig-1",
        )])
        # A later poll recomputes the win-prob but carries no new read (no sig change).
        repo.upsert_matches(sqlite_session, [_match(
            1, live_winprob_json={"home": 60, "draw": 22, "away": 18},
        )])
        row = sqlite_session.execute(
            sa.select(repo.matches_table).where(repo.matches_table.c.fixture_id == 1)
        ).mappings().first()
        assert row["live_winprob_json"] == {"home": 60, "draw": 22, "away": 18}  # overwritten
        assert row["live_read_text"] == "Early read."  # keep-last-good, not clobbered

    def test_group_name_not_clobbered_by_none_payload(self, sqlite_session):
        # The daily collect assigns group_name; the live poller's payloads carry
        # None. A None payload must NOT null the stored group — otherwise the live
        # win-prob/read path (gated on group_name) silently disables mid-match.
        repo.upsert_matches(sqlite_session, [_match(1, group_name="A")])
        repo.upsert_matches(sqlite_session, [_match(1, group_name=None)])  # a live poll
        row = sqlite_session.execute(
            sa.select(repo.matches_table).where(repo.matches_table.c.fixture_id == 1)
        ).mappings().first()
        assert row["group_name"] == "A"  # keep-last-good, not clobbered to NULL

    def test_group_name_updates_when_payload_carries_it(self, sqlite_session):
        # A real group_name in the payload still updates (e.g. a corrected mapping).
        repo.upsert_matches(sqlite_session, [_match(1, group_name="A")])
        repo.upsert_matches(sqlite_session, [_match(1, group_name="B")])
        row = sqlite_session.execute(
            sa.select(repo.matches_table).where(repo.matches_table.c.fixture_id == 1)
        ).mappings().first()
        assert row["group_name"] == "B"


def _factory_with_status(rows_with_status):
    """Session factory whose stored rows include `status` (and optionally `kickoff_utc`).
    Used by finalize-on-drop tests."""
    return lambda: FakeSession(rows_with_status)


class TestFinalizeOnDrop:
    """When a match we have stored as in-play disappears from ?live=all,
    collect_live must fetch the full fixture set once and upsert the real
    final status so the match stops showing as 'live' until the daily collect."""

    def test_stuck_match_is_finalized_from_full_fetch(self, captured_upsert):
        # Fixture 42 is stored as "2H" but absent from the live feed → stuck.
        # Full fetch returns it as "FT" → upserted with the real final status.
        full_match = FakeMatch(42, status="FT", home_score=2, away_score=1)
        stored = [_stored_row(42, status="2H")]
        client = FakeClient(live=[], full=[full_match])
        collect.collect_live(_factory_with_status(stored), client)
        assert client.full_fetch_calls == 1
        assert captured_upsert["rows"][0].fixture_id == 42
        assert captured_upsert["rows"][0].status == "FT"

    def test_live_match_not_double_finalized(self, captured_upsert):
        # Fixture 7 is both in DB (status="2H") and in the live feed → normal upsert only.
        live_m = FakeMatch(7, status="2H")
        stored = [_stored_row(7, status="2H")]
        client = FakeClient(live=[live_m], full=None)
        collect.collect_live(_factory_with_status(stored), client)
        # Full fetch must NOT be called when no fixtures are stuck.
        assert client.full_fetch_calls == 0
        assert captured_upsert["rows"][0].fixture_id == 7

    def test_no_full_fetch_when_nothing_stuck(self, captured_upsert):
        # No stored fixtures at all → nothing is stuck → no full fetch.
        client = FakeClient(live=[], full=None)
        collect.collect_live(_factory_with_status([]), client)
        assert client.full_fetch_calls == 0

    def test_full_fetch_failure_does_not_abort_normal_poll(self, captured_upsert, monkeypatch):
        # If the full fetch raises, the normal live poll must still complete.
        live_m = FakeMatch(5, status="1H")
        stored = [
            _stored_row(5, status="1H"),   # in live feed → normal
            _stored_row(99, status="2H"),  # stuck → triggers full fetch
        ]

        def boom(live=False):
            if not live:
                raise RuntimeError("full fetch failed")
            return [live_m]

        client = FakeClient(live=[live_m])
        client.get_fixtures = boom
        collect.collect_live(_factory_with_status(stored), client)
        # Normal match still upserted despite full-fetch failure.
        assert any(r.fixture_id == 5 for r in captured_upsert["rows"])
