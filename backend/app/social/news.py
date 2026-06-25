"""News-media source: recent articles about a fixture from RSS/Atom feeds listed
in a config file (app/social/news_feeds.json, overridable via SOCIAL_NEWS_FEEDS_FILE).

Unlike Reddit/Bluesky (query search), a feed returns a publisher's whole stream,
so we filter client-side to entries mentioning either team before handing them to
curation. No credentials — available whenever the config has ≥1 valid feed."""
from __future__ import annotations

import calendar
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import feedparser
import httpx

from app.config import settings
from app.social.base import HTTP_TIMEOUT, Candidate, is_http_url

log = logging.getLogger(__name__)

_DEFAULT_FEEDS_FILE = Path(__file__).with_name("news_feeds.json")
_TAG_RE = re.compile(r"<[^>]+>")
_MAX_TEXT = 500


def _load_feeds() -> list[dict]:
    """Read + validate the feed config: a JSON object {"feeds": [{name, url}]} or a
    bare list. Drops entries without an http(s) url. Missing/malformed file → []."""
    path = Path(settings.SOCIAL_NEWS_FEEDS_FILE) if settings.SOCIAL_NEWS_FEEDS_FILE else _DEFAULT_FEEDS_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("News feeds config unreadable (%s): %s", path, exc)
        return []
    feeds = data.get("feeds") if isinstance(data, dict) else data
    return [f for f in (feeds or []) if isinstance(f, dict) and is_http_url(f.get("url"))]


def _strip_html(text: str) -> str:
    """Feed summaries often carry HTML; flatten to plain text + collapse whitespace."""
    return " ".join(_TAG_RE.sub(" ", text or "").split())


def _entry_datetime(entry: Any) -> Optional[datetime]:
    """feedparser normalizes dates to a GMT struct_time; convert to aware UTC.
    `calendar.timegm` (not time.mktime) so the struct_time is read as UTC."""
    st = entry.get("published_parsed") or entry.get("updated_parsed")
    if not st:
        return None
    try:
        return datetime.fromtimestamp(calendar.timegm(st), tz=timezone.utc)
    except (ValueError, OverflowError, TypeError):
        return None


def entries_to_candidates(
    entries: list, feed_name: str, terms: list[str], since: datetime
) -> list[Candidate]:
    """Pure: filter parsed feed entries to those mentioning a team (in title or
    summary) and newer than `since`, mapped to Candidates. Entries with no date
    are kept (some feeds omit it). Separated from I/O so it is unit-tested."""
    out: list[Candidate] = []
    for entry in entries:
        title = (entry.get("title") or "").strip()
        link = entry.get("link")
        if not title or not is_http_url(link):
            continue
        summary = _strip_html(entry.get("summary") or "")
        blob = f"{title} {summary}".lower()
        if terms and not any(t in blob for t in terms):
            continue
        posted = _entry_datetime(entry)
        if posted and posted < since:
            continue
        text = title if not summary else f"{title} — {summary}"
        out.append(
            Candidate(
                source="news",
                url=link,
                author=feed_name,
                posted_at=posted.isoformat() if posted else None,
                text=text[:_MAX_TEXT],
                engagement=0,
            )
        )
    return out


class NewsSource:
    name = "news"

    def __init__(self) -> None:
        self._feeds = _load_feeds()

    def available(self) -> bool:
        return bool(self._feeds)

    def fetch(self, home: str, away: str, since: datetime) -> list[Candidate]:
        terms = [t.lower() for t in (home, away) if t]
        out: list[Candidate] = []
        for feed in self._feeds:
            out.extend(self._fetch_one(feed, terms, since))
        return out

    def _fetch_one(self, feed: dict, terms: list[str], since: datetime) -> list[Candidate]:
        url = feed["url"]
        name = feed.get("name") or url
        # feedparser has no network timeout, so fetch bytes via httpx (bounded) and
        # parse offline — a slow host can never stall the daily batch.
        try:
            resp = httpx.get(
                url,
                timeout=HTTP_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": settings.REDDIT_USER_AGENT},
            )
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
        except Exception as exc:  # noqa: BLE001 — one bad feed ≠ skip the rest
            log.warning("News feed %s failed: %s", url, exc)
            return []
        return entries_to_candidates(parsed.entries, name, terms, since)
