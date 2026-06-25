"""Reddit source — OAuth2 client-credentials → /search over r/worldcup+r/soccer.

Free: a Reddit "script" app (client id/secret) authenticates with the
client-credentials grant; no user context needed for public search. The raw
network call is isolated in `_search_raw` so mapping/filtering is unit-tested
without httpx."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.config import settings
from app.social.base import HTTP_TIMEOUT, Candidate, build_query, is_http_url

log = logging.getLogger(__name__)

_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_SUBREDDITS = "worldcup+soccer"
_LIMIT = 25


class RedditSource:
    name = "reddit"

    def available(self) -> bool:
        return bool(settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET)

    def _token(self) -> Optional[str]:
        resp = httpx.post(
            _TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(settings.REDDIT_CLIENT_ID or "", settings.REDDIT_CLIENT_SECRET or ""),
            headers={"User-Agent": settings.REDDIT_USER_AGENT},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")

    def _search_raw(self, query: str) -> dict[str, Any]:
        """Authenticated /search call. Isolated for test monkeypatching."""
        token = self._token()
        if not token:
            return {}
        resp = httpx.get(
            f"https://oauth.reddit.com/r/{_SUBREDDITS}/search",
            params={"q": query, "sort": "new", "t": "week", "limit": _LIMIT, "restrict_sr": "true"},
            headers={
                "Authorization": f"bearer {token}",
                "User-Agent": settings.REDDIT_USER_AGENT,
            },
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
            log.warning("Reddit fetch failed: %s", exc)
            return []
        return _map(data, since)


def _map(data: dict[str, Any], since: datetime) -> list[Candidate]:
    out: list[Candidate] = []
    for child in (data.get("data", {}) or {}).get("children", []) or []:
        d = child.get("data", {}) or {}
        created = d.get("created_utc")
        posted_at: Optional[str] = None
        if isinstance(created, (int, float)):
            dt = datetime.fromtimestamp(created, tz=timezone.utc)
            if dt < since:
                continue
            posted_at = dt.isoformat()
        permalink = d.get("permalink")
        url = f"https://www.reddit.com{permalink}" if permalink else d.get("url")
        if not is_http_url(url):
            continue
        text = " ".join(part for part in (d.get("title"), d.get("selftext")) if part).strip()
        if not text:
            continue
        author = d.get("author") or "unknown"
        out.append(Candidate(
            source="reddit",
            url=url,
            author=f"u/{author}" if not author.startswith("u/") else author,
            posted_at=posted_at,
            text=text,
            engagement=int(d.get("score") or 0),
        ))
    return out
