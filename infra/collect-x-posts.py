#!/usr/bin/env python3
"""Collect X (Twitter) posts about upcoming fixtures using YOUR logged-in browser,
and write x_candidates.json for upload to the VM (see infra/upload-x-candidates.sh).

WHY THIS EXISTS: X's API is paid, so this drives a real browser session instead.

⚠️  READ BEFORE USING:
  - Automating X is against X's Terms of Service. Running this against your own
    account can get it rate-limited or suspended. Use a low cadence (nightly),
    keep volumes small, and accept the risk for your own account/product.
  - X changes its DOM often; the selectors below WILL drift. Treat them as a
    starting point and adjust when extraction returns nothing.
  - This does NOT solve CAPTCHAs or evade bot-detection. If X challenges you,
    stop and solve it manually in the browser, then re-run.

SETUP (once):
    pip install playwright
    playwright install chromium
  Then log into x.com in the dedicated profile dir the first run opens
  (--profile, default ./.x-profile), so the session cookie persists.

RUN:
    # fixtures.json: [{"fixture_id":123,"home_team":"Brazil","away_team":"Serbia"}, ...]
    # Produce it with infra/upload-x-candidates.sh --fetch-fixtures > fixtures.json
    python3 infra/collect-x-posts.py --fixtures fixtures.json --out x_candidates.json

Then upload:  ./infra/upload-x-candidates.sh x_candidates.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

# Tunables — adjust cadence/limits to stay gentle on X.
POSTS_PER_FIXTURE = 5
PAGE_SETTLE_SECONDS = 4.0
BETWEEN_FIXTURES_SECONDS = 8.0
NAV_TIMEOUT_MS = 30_000


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _search_url(home: str, away: str) -> str:
    # Latest tab, English; quote the team pair so it stays one query.
    q = quote(f'{home} {away} (World Cup OR WC2026)')
    return f"https://x.com/search?q={q}&src=typed_query&f=live"


def _extract_posts(page, limit: int) -> list[dict]:
    """Pull up to `limit` posts from a search results page. Selectors target the
    public article structure; update them here when X changes its markup."""
    posts: list[dict] = []
    articles = page.locator('article[data-testid="tweet"]')
    count = min(articles.count(), limit * 3)  # over-scan; many are ads/reposts
    seen: set[str] = set()
    for i in range(count):
        if len(posts) >= limit:
            break
        art = articles.nth(i)
        try:
            text = art.locator('[data-testid="tweetText"]').first.inner_text(timeout=2000)
        except Exception:
            continue
        # Permalink + handle.
        url, author = "", "X user"
        try:
            href = art.locator('a[href*="/status/"]').first.get_attribute("href", timeout=2000)
            if href:
                url = "https://x.com" + href.split("?")[0]
                author = "@" + href.lstrip("/").split("/")[0]
        except Exception:
            pass
        if not text.strip() or not url or url in seen:
            continue
        seen.add(url)
        posts.append({
            "author": author,
            "url": url,
            "text": " ".join(text.split())[:500],
            "posted_at": None,        # timestamps are unreliable to scrape; curation tolerates None
            "engagement": 0,           # left 0; curation ranks on relevance, not likes
        })
    return posts


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect X posts for upcoming fixtures.")
    ap.add_argument("--fixtures", required=True, help="JSON file: [{fixture_id, home_team, away_team}]")
    ap.add_argument("--out", default="x_candidates.json")
    ap.add_argument("--profile", default="./.x-profile", help="Persistent Chrome profile dir (log into X here once)")
    ap.add_argument("--headed", action="store_true", help="Show the browser (needed for first-time login / challenges)")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run: pip install playwright && playwright install chromium", file=sys.stderr)
        return 1

    fixtures = json.loads(Path(args.fixtures).read_text(encoding="utf-8"))
    if not isinstance(fixtures, list) or not fixtures:
        print("fixtures file must be a non-empty JSON list", file=sys.stderr)
        return 1

    out: dict[str, list[dict]] = {}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(args.profile, headless=not args.headed)
        page = ctx.new_page()
        page.set_default_navigation_timeout(NAV_TIMEOUT_MS)
        for fx in fixtures:
            home, away = fx.get("home_team"), fx.get("away_team")
            fid = fx.get("fixture_id")
            if not (home and away and fid):
                continue
            try:
                page.goto(_search_url(home, away))
                time.sleep(PAGE_SETTLE_SECONDS)
                posts = _extract_posts(page, POSTS_PER_FIXTURE)
            except Exception as exc:  # noqa: BLE001 — one fixture failing ≠ abort the run
                print(f"  ! {home} vs {away}: {exc}", file=sys.stderr)
                posts = []
            if posts:
                out[str(fid)] = posts
            print(f"  {home} vs {away}: {len(posts)} posts", file=sys.stderr)
            time.sleep(BETWEEN_FIXTURES_SECONDS)
        ctx.close()

    Path(args.out).write_text(
        json.dumps({"collected_at": _now_iso(), "fixtures": out}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {args.out}: {sum(len(v) for v in out.values())} posts across {len(out)} fixtures.", file=sys.stderr)
    if not out:
        print("No posts extracted — X markup likely changed; update selectors in _extract_posts().", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
