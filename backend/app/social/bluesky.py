"""Bluesky source — AT Protocol createSession → app.bsky.feed.searchPosts.

Free: an account handle + app password create a session JWT used to call the
search endpoint. The raw network call is isolated in `_search_raw` so
mapping/filtering is unit-tested without httpx."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from app.config import settings
from app.social.base import HTTP_TIMEOUT, Candidate, build_query, is_http_url

log = logging.getLogger(__name__)

_BASE = "https://bsky.social/xrpc"
_SESSION_URL = f"{_BASE}/com.atproto.server.createSession"
_SEARCH_URL = f"{_BASE}/app.bsky.feed.searchPosts"
_LIMIT = 25


class BlueskySource:
    name = "bluesky"

    def available(self) -> bool:
        return bool(settings.BLUESKY_IDENTIFIER and settings.BLUESKY_APP_PASSWORD)

    def _token(self) -> Optional[str]:
        resp = httpx.post(
            _SESSION_URL,
            json={
                "identifier": settings.BLUESKY_IDENTIFIER,
                "password": settings.BLUESKY_APP_PASSWORD,
            },
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("accessJwt")

    def _search_raw(self, query: str) -> dict[str, Any]:
        """Authenticated searchPosts call. Isolated for test monkeypatching."""
        token = self._token()
        if not token:
            return {}
        resp = httpx.get(
            _SEARCH_URL,
            params={"q": query, "sort": "latest", "limit": _LIMIT},
            headers={"Authorization": f"Bearer {token}"},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def fetch(self, home: str, away: str, since: datetime) -> list[Candidate]:
        if not self.available():
            return []
        try:
            data = self._search_raw(build_query(home, away))
        except Exception as exc:  # noqa: BLE001 — degrade to empty, never raise
            log.warning("Bluesky fetch failed: %s", exc)
            return []
        return _map(data, since)


def _post_url(uri: Optional[str], handle: Optional[str]) -> Optional[str]:
    """Build the public bsky.app post url from the at:// uri + author handle."""
    if not uri or not handle:
        return None
    rkey = uri.rstrip("/").split("/")[-1]
    if not rkey:
        return None
    return f"https://bsky.app/profile/{handle}/post/{rkey}"


def _parse_dt(value: Any, since: datetime) -> tuple[bool, Optional[str]]:
    """(keep, posted_at_iso). Drops posts older than `since`; unknown dates kept."""
    if not isinstance(value, str):
        return True, None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True, None
    if dt < since:
        return False, None
    return True, dt.isoformat()


def _map(data: dict[str, Any], since: datetime) -> list[Candidate]:
    out: list[Candidate] = []
    for post in data.get("posts", []) or []:
        record = post.get("record", {}) or {}
        text = (record.get("text") or "").strip()
        if not text:
            continue
        author_obj = post.get("author", {}) or {}
        handle = author_obj.get("handle")
        url = _post_url(post.get("uri"), handle)
        if not is_http_url(url):
            continue
        keep, posted_at = _parse_dt(post.get("indexedAt"), since)
        if not keep:
            continue
        engagement = int(post.get("likeCount") or 0) + int(post.get("repostCount") or 0)
        out.append(Candidate(
            source="bluesky",
            url=url,
            author=handle or "unknown",
            posted_at=posted_at,
            text=text,
            engagement=engagement,
        ))
    return out
