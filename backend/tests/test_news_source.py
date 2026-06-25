"""Unit tests for the news social source's pure logic (no network). The fetch
path is thin I/O over feedparser; the filtering/mapping that matters is tested
directly via entries_to_candidates + the helpers."""

import calendar
import time
from datetime import datetime, timedelta, timezone

from app.social.news import (
    _entry_datetime,
    _load_feeds,
    _strip_html,
    entries_to_candidates,
)

NOW = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)
SINCE = NOW - timedelta(hours=48)


def _entry(title, link="https://news.example/a", summary="", when=NOW):
    return {
        "title": title,
        "link": link,
        "summary": summary,
        "published_parsed": time.gmtime(calendar.timegm(when.timetuple())),
    }


class TestEntriesToCandidates:
    def test_keeps_entry_mentioning_a_team(self):
        entries = [_entry("Brazil name squad for Spain clash")]
        out = entries_to_candidates(entries, "BBC", ["brazil", "spain"], SINCE)
        assert len(out) == 1
        assert out[0].source == "news"
        assert out[0].author == "BBC"
        assert out[0].url == "https://news.example/a"

    def test_drops_entry_not_mentioning_either_team(self):
        entries = [_entry("France beat Germany in friendly")]
        assert entries_to_candidates(entries, "BBC", ["brazil", "spain"], SINCE) == []

    def test_matches_team_in_summary(self):
        entries = [_entry("Match preview", summary="A look at the Spain backline")]
        assert len(entries_to_candidates(entries, "BBC", ["spain"], SINCE)) == 1

    def test_drops_entry_older_than_since(self):
        old = _entry("Brazil report", when=NOW - timedelta(hours=72))
        assert entries_to_candidates([old], "BBC", ["brazil"], SINCE) == []

    def test_skips_entry_without_title_or_http_link(self):
        entries = [
            _entry("", link="https://news.example/x"),
            _entry("Brazil news", link="javascript:alert(1)"),
        ]
        assert entries_to_candidates(entries, "BBC", ["brazil"], SINCE) == []

    def test_no_terms_keeps_everything_recent(self):
        entries = [_entry("Any headline")]
        assert len(entries_to_candidates(entries, "BBC", [], SINCE)) == 1


class TestHelpers:
    def test_strip_html(self):
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_entry_datetime_reads_struct_as_utc(self):
        e = _entry("x", when=NOW)
        assert _entry_datetime(e) == NOW

    def test_entry_datetime_none_when_absent(self):
        assert _entry_datetime({"title": "x"}) is None

    def test_bundled_feeds_config_loads(self):
        # The committed app/social/news_feeds.json must parse and expose feeds.
        feeds = _load_feeds()
        assert len(feeds) >= 1
        assert all(f["url"].startswith("http") for f in feeds)
