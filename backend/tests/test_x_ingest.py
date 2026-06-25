"""Unit tests for X candidate ingestion (load + validate + anti-stale). No I/O
beyond a tmp file written by the test."""

import json
from datetime import datetime, timedelta, timezone

from app.social.x_ingest import load_x_candidates

NOW = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)


def _write(tmp_path, obj):
    p = tmp_path / "x_candidates.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return str(p)


def _payload(collected=NOW, items=None):
    return {
        "collected_at": collected.isoformat(),
        "fixtures": {"1489410": items if items is not None else [
            {"author": "@fan", "url": "https://x.com/fan/1", "text": "great match incoming",
             "posted_at": (NOW - timedelta(hours=2)).isoformat(), "engagement": 50},
        ]},
    }


def test_loads_valid_candidates(tmp_path):
    path = _write(tmp_path, _payload())
    out = load_x_candidates(path, now=NOW, max_age_hours=36)
    assert set(out) == {1489410}
    c = out[1489410][0]
    assert c.source == "x" and c.author == "@fan" and c.engagement == 50


def test_unset_or_missing_path_returns_empty():
    assert load_x_candidates(None, now=NOW, max_age_hours=36) == {}
    assert load_x_candidates("/no/such/file.json", now=NOW, max_age_hours=36) == {}


def test_stale_file_ignored(tmp_path):
    path = _write(tmp_path, _payload(collected=NOW - timedelta(hours=48)))
    assert load_x_candidates(path, now=NOW, max_age_hours=36) == {}


def test_drops_items_without_text_or_http_url(tmp_path):
    path = _write(tmp_path, _payload(items=[
        {"author": "@a", "url": "https://x.com/a", "text": ""},
        {"author": "@b", "url": "javascript:alert(1)", "text": "bad scheme"},
        {"author": "@c", "url": "https://x.com/c", "text": "kept"},
    ]))
    out = load_x_candidates(path, now=NOW, max_age_hours=36)
    assert [c.url for c in out[1489410]] == ["https://x.com/c"]


def test_malformed_json_returns_empty(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    assert load_x_candidates(str(p), now=NOW, max_age_hours=36) == {}


def test_non_integer_fixture_key_skipped(tmp_path):
    path = _write(tmp_path, {"collected_at": NOW.isoformat(),
                             "fixtures": {"abc": [{"url": "https://x.com/x", "text": "t"}]}})
    assert load_x_candidates(path, now=NOW, max_age_hours=36) == {}
