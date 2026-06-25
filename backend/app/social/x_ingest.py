"""Ingest X (Twitter) candidates collected out-of-band.

X's API is paid, so X posts are gathered by a local browser script (see
infra/collect-x-posts.py), uploaded to the VM as a JSON file, and read here. This
module just loads + validates that file into Candidates keyed by fixture id — no
network. A stale file (older than max_age_hours) is ignored so a dead nightly job
never keeps resurfacing old posts.

File shape:
  {
    "collected_at": "2026-06-25T09:00:00Z",   # ISO-8601 UTC
    "fixtures": {
      "1489410": [
        {"author": "@handle", "url": "https://x.com/...", "text": "...",
         "posted_at": "2026-06-25T08:10:00Z", "engagement": 120}
      ]
    }
  }
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.social.base import Candidate, is_http_url

log = logging.getLogger(__name__)

_MAX_TEXT = 500


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def load_x_candidates(
    path: Optional[str], *, now: datetime, max_age_hours: int
) -> dict[int, list[Candidate]]:
    """Load X candidates keyed by fixture id. Returns {} when the path is unset,
    missing, malformed, or the file is older than `max_age_hours` (anti-stale)."""
    if not path:
        return {}
    try:
        data = json.loads(open(path, encoding="utf-8").read())
    except (OSError, ValueError) as exc:
        log.warning("X candidates file unreadable (%s): %s", path, exc)
        return {}
    if not isinstance(data, dict):
        return {}

    collected = _parse_dt(data.get("collected_at"))
    if collected is not None:
        age_h = (now - collected).total_seconds() / 3600
        if age_h > max_age_hours:
            log.info("X candidates file is stale (%.1fh > %dh) — ignoring", age_h, max_age_hours)
            return {}

    out: dict[int, list[Candidate]] = {}
    for fid_raw, items in (data.get("fixtures") or {}).items():
        try:
            fid = int(fid_raw)
        except (TypeError, ValueError):
            continue
        cands: list[Candidate] = []
        for it in items or []:
            if not isinstance(it, dict):
                continue
            url, text = it.get("url"), (it.get("text") or "").strip()
            if not text or not is_http_url(url):
                continue
            posted = _parse_dt(it.get("posted_at"))
            try:
                engagement = int(it.get("engagement") or 0)
            except (TypeError, ValueError):
                engagement = 0
            cands.append(
                Candidate(
                    source="x",
                    url=url,
                    author=(it.get("author") or "X user").strip(),
                    posted_at=posted.isoformat() if posted else None,
                    text=text[:_MAX_TEXT],
                    engagement=max(0, engagement),
                )
            )
        if cands:
            out[fid] = cands
    return out
