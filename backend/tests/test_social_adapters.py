"""Unit tests for the social source adapters + shared plumbing.

No real network: each source's raw fetch is monkeypatched to return canned JSON
so mapping/filtering is exercised in isolation. Credential gating and
error-to-empty degradation are asserted directly.
"""
from datetime import datetime, timezone

from app.social.base import Candidate, build_query, dedupe, is_http_url, pretrim
from app.social.bluesky import BlueskySource
from app.social.reddit import RedditSource

SINCE = datetime(2026, 6, 23, 0, 0, tzinfo=timezone.utc)
RECENT = datetime(2026, 6, 24, 9, 0, tzinfo=timezone.utc)
OLD = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)


# --- shared helpers --------------------------------------------------------

def test_build_query():
    assert build_query("Brazil", "Serbia") == "Brazil Serbia World Cup"


def test_is_http_url_rejects_nonhttp():
    assert is_http_url("https://x.com/a")
    assert is_http_url("http://x.com/a")
    assert not is_http_url("javascript:alert(1)")
    assert not is_http_url("data:text/html,x")
    assert not is_http_url(None)


def _c(url, text, eng=0, source="reddit"):
    return Candidate(source=source, url=url, author="a", text=text, engagement=eng)


def test_dedupe_by_url_and_text():
    cands = [
        _c("https://r.com/1", "great match"),
        _c("https://r.com/1/", "great match"),          # same url (trailing slash)
        _c("https://b.com/2", "GREAT   match", eng=5, source="bluesky"),  # same text, higher eng
    ]
    out = dedupe(cands)
    assert len(out) == 1
    assert out[0].engagement == 5  # higher-engagement duplicate wins


def test_pretrim_orders_by_engagement_and_caps():
    cands = [_c(f"https://r.com/{i}", f"t{i}", eng=i) for i in range(5)]
    out = pretrim(cands, cap=3)
    assert [c.engagement for c in out] == [4, 3, 2]


# --- Reddit ----------------------------------------------------------------

def _reddit_payload():
    return {
        "data": {
            "children": [
                {"data": {
                    "title": "Brazil look sharp",
                    "selftext": "their press is elite",
                    "permalink": "/r/worldcup/comments/abc",
                    "author": "fan1",
                    "created_utc": RECENT.timestamp(),
                    "score": 42,
                }},
                {"data": {  # too old → dropped
                    "title": "old take",
                    "permalink": "/r/worldcup/comments/old",
                    "author": "fan2",
                    "created_utc": OLD.timestamp(),
                    "score": 10,
                }},
            ]
        }
    }


def test_reddit_maps_fields(monkeypatch):
    src = RedditSource()
    monkeypatch.setattr(src, "available", lambda: True)
    monkeypatch.setattr(src, "_search_raw", lambda q: _reddit_payload())
    out = src.fetch("Brazil", "Serbia", SINCE)
    assert len(out) == 1
    c = out[0]
    assert c.source == "reddit"
    assert c.url == "https://www.reddit.com/r/worldcup/comments/abc"
    assert c.author == "u/fan1"
    assert c.engagement == 42
    assert "press is elite" in c.text


def test_reddit_unavailable_without_creds(monkeypatch):
    src = RedditSource()
    monkeypatch.setattr(src, "available", lambda: False)
    assert src.fetch("A", "B", SINCE) == []


def test_reddit_network_error_returns_empty(monkeypatch):
    src = RedditSource()
    monkeypatch.setattr(src, "available", lambda: True)

    def boom(q):
        raise RuntimeError("429")

    monkeypatch.setattr(src, "_search_raw", boom)
    assert src.fetch("A", "B", SINCE) == []


# --- Bluesky ---------------------------------------------------------------

def _bsky_payload():
    return {
        "posts": [
            {
                "uri": "at://did:plc:xyz/app.bsky.feed.post/rkey123",
                "author": {"handle": "fan.bsky.social"},
                "record": {"text": "Serbia counter is dangerous"},
                "indexedAt": RECENT.isoformat(),
                "likeCount": 7,
                "repostCount": 3,
            },
            {  # missing text → dropped
                "uri": "at://did:plc:xyz/app.bsky.feed.post/empty",
                "author": {"handle": "x.bsky.social"},
                "record": {"text": "  "},
                "indexedAt": RECENT.isoformat(),
            },
        ]
    }


def test_bluesky_maps_fields(monkeypatch):
    src = BlueskySource()
    monkeypatch.setattr(src, "available", lambda: True)
    monkeypatch.setattr(src, "_search_raw", lambda q: _bsky_payload())
    out = src.fetch("Brazil", "Serbia", SINCE)
    assert len(out) == 1
    c = out[0]
    assert c.source == "bluesky"
    assert c.url == "https://bsky.app/profile/fan.bsky.social/post/rkey123"
    assert c.author == "fan.bsky.social"
    assert c.engagement == 10  # likes + reposts
    assert "counter is dangerous" in c.text


def test_bluesky_drops_old_post(monkeypatch):
    src = BlueskySource()
    payload = {
        "posts": [{
            "uri": "at://did/app.bsky.feed.post/r",
            "author": {"handle": "h.bsky.social"},
            "record": {"text": "stale"},
            "indexedAt": OLD.isoformat(),
            "likeCount": 1,
        }]
    }
    monkeypatch.setattr(src, "available", lambda: True)
    monkeypatch.setattr(src, "_search_raw", lambda q: payload)
    assert src.fetch("A", "B", SINCE) == []


def test_bluesky_unavailable_without_creds(monkeypatch):
    src = BlueskySource()
    monkeypatch.setattr(src, "available", lambda: False)
    assert src.fetch("A", "B", SINCE) == []
