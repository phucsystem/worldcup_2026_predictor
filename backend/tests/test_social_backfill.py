"""Unit tests for backfill_social_highlights.

Sources, curation, and the DB write are all mocked — no network/LLM/DB. The real
select_fixtures_needing_social runs so window/cap/refresh behavior is exercised
end-to-end through the backfill.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import app.data.collect as collect
import app.social.bluesky as bluesky_mod
import app.social.news as news_mod
import app.social.reddit as reddit_mod
import app.social.select as select_mod
from app.config import settings
from app.data.models import Match
from app.social.base import Candidate

NOW_ISH = datetime.now(tz=timezone.utc)


def _match(fid, *, kickoff_offset_h=6, status="NS", group="G", social=None):
    return Match(
        fixture_id=fid, group_name=group, home_team="Brazil", away_team="Serbia",
        home_score=None, away_score=None, status=status,
        kickoff_utc=NOW_ISH + timedelta(hours=kickoff_offset_h), social_json=social,
    )


class _FakeSource:
    def __init__(self, name, *, avail=True, raises=False, cands=None):
        self.name = name
        self._avail = avail
        self._raises = raises
        self._cands = cands or []

    def available(self):
        return self._avail

    def fetch(self, home, away, since):
        if self._raises:
            raise RuntimeError(f"{self.name} down")
        return list(self._cands)


@contextmanager
def _fake_factory():
    yield object()  # dummy session; upsert_matches is mocked so it's never used


def _install(monkeypatch, *, reddit, bluesky, curate, key="k", news=None):
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", key)
    monkeypatch.setattr(reddit_mod, "RedditSource", lambda: reddit)
    monkeypatch.setattr(bluesky_mod, "BlueskySource", lambda: bluesky)
    # Default the news source to unavailable so these Reddit/Bluesky-focused tests
    # are unaffected by the bundled feeds config; pass news=_FakeSource(...) to test it.
    monkeypatch.setattr(news_mod, "NewsSource", lambda: news or _FakeSource("news", avail=False))
    monkeypatch.setattr(select_mod, "generate_social_highlights", curate)
    stored = []
    monkeypatch.setattr(collect, "upsert_matches", lambda session, ms: stored.extend(ms))
    return stored


def _cand(url="https://r.com/1"):
    return Candidate(source="reddit", url=url, author="u/x", text="great insight", engagement=5)


def test_no_source_available_returns_zero_no_write(monkeypatch):
    stored = _install(
        monkeypatch,
        reddit=_FakeSource("reddit", avail=False),
        bluesky=_FakeSource("bluesky", avail=False),
        curate=lambda h, a, c: ({"highlights": [{"x": 1}]}, "m"),
    )
    assert collect.backfill_social_highlights(_fake_factory, [_match(1)]) == 0
    assert stored == []


def test_no_api_key_returns_zero(monkeypatch):
    stored = _install(
        monkeypatch,
        reddit=_FakeSource("reddit", cands=[_cand()]),
        bluesky=_FakeSource("bluesky", avail=False),
        curate=lambda h, a, c: ({"highlights": [{"x": 1}]}, "m"),
        key=None,
    )
    assert collect.backfill_social_highlights(_fake_factory, [_match(1)]) == 0
    assert stored == []


def test_successful_curation_stores_blob(monkeypatch):
    blob = {"highlights": [{"source": "reddit", "url": "https://r.com/1",
                            "author": "u/x", "text": "great", "why": "insight"}]}
    stored = _install(
        monkeypatch,
        reddit=_FakeSource("reddit", cands=[_cand()]),
        bluesky=_FakeSource("bluesky", avail=False),
        curate=lambda h, a, c: (blob, "deepseek-chat"),
    )
    n = collect.backfill_social_highlights(_fake_factory, [_match(1)])
    assert n == 1
    assert stored[0].social_json == blob
    assert stored[0].social_model == "deepseek-chat"


def test_one_source_raising_other_still_used(monkeypatch):
    captured = {}

    def curate(home, away, candidates):
        captured["n"] = len(candidates)
        return ({"highlights": [{"source": "bluesky", "url": "https://b/1",
                                 "author": "h", "text": "t", "why": "w"}]}, "m")

    _install(
        monkeypatch,
        reddit=_FakeSource("reddit", raises=True),
        bluesky=_FakeSource("bluesky", cands=[_cand("https://b/1")]),
        curate=curate,
    )
    n = collect.backfill_social_highlights(_fake_factory, [_match(1)])
    assert n == 1
    assert captured["n"] == 1  # bluesky candidate survived the reddit failure


def test_news_only_drives_backfill(monkeypatch):
    # News needs no credentials: with Reddit + Bluesky unavailable, an available
    # news source alone still collects + curates highlights.
    blob = {"highlights": [{"source": "news", "url": "https://n/1",
                            "author": "BBC", "text": "report", "why": "news"}]}
    stored = _install(
        monkeypatch,
        reddit=_FakeSource("reddit", avail=False),
        bluesky=_FakeSource("bluesky", avail=False),
        news=_FakeSource("news", cands=[Candidate(
            source="news", url="https://n/1", author="BBC", text="report")]),
        curate=lambda h, a, c: (blob, "deepseek-chat"),
    )
    assert collect.backfill_social_highlights(_fake_factory, [_match(1)]) == 1
    assert stored[0].social_json == blob


def test_empty_curation_keeps_last_good(monkeypatch):
    stored = _install(
        monkeypatch,
        reddit=_FakeSource("reddit", cands=[_cand()]),
        bluesky=_FakeSource("bluesky", avail=False),
        curate=lambda h, a, c: None,  # keep-last-good
    )
    assert collect.backfill_social_highlights(_fake_factory, [_match(1, social={"highlights": []})]) == 0
    assert stored == []


def test_curation_failure_skips_fixture(monkeypatch):
    def boom(h, a, c):
        raise RuntimeError("LLM down")

    stored = _install(
        monkeypatch,
        reddit=_FakeSource("reddit", cands=[_cand()]),
        bluesky=_FakeSource("bluesky", avail=False),
        curate=boom,
    )
    assert collect.backfill_social_highlights(_fake_factory, [_match(1)]) == 0
    assert stored == []


def test_fanout_capped_to_max_per_run(monkeypatch):
    calls = {"n": 0}

    def curate(h, a, c):
        calls["n"] += 1
        return ({"highlights": [{"source": "reddit", "url": "https://r/1",
                                 "author": "u", "text": "t", "why": "w"}]}, "m")

    _install(
        monkeypatch,
        reddit=_FakeSource("reddit", cands=[_cand()]),
        bluesky=_FakeSource("bluesky", avail=False),
        curate=curate,
    )
    cap = settings.SOCIAL_MAX_FIXTURES_PER_RUN
    # cap + 5 in-window upcoming fixtures; only `cap` should be curated.
    matches = [_match(i, kickoff_offset_h=1 + i) for i in range(cap + 5)]
    n = collect.backfill_social_highlights(_fake_factory, matches)
    assert n == cap
    assert calls["n"] == cap


def test_finished_fixture_not_targeted(monkeypatch):
    stored = _install(
        monkeypatch,
        reddit=_FakeSource("reddit", cands=[_cand()]),
        bluesky=_FakeSource("bluesky", avail=False),
        curate=lambda h, a, c: ({"highlights": [{"source": "reddit", "url": "https://r/1",
                                                 "author": "u", "text": "t", "why": "w"}]}, "m"),
    )
    assert collect.backfill_social_highlights(_fake_factory, [_match(1, status="FT")]) == 0
    assert stored == []
