from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://wc:wc@localhost:5432/worldcup"
    API_FOOTBALL_KEY: Optional[str] = None
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"
    # FIFA World Cup = league 1. Season 2026 is the target; the API-Football free
    # plan only covers 2021–2023, so set API_FOOTBALL_SEASON=2022 for real demo data.
    API_FOOTBALL_LEAGUE: int = 1
    API_FOOTBALL_SEASON: int = 2026
    DEEPSEEK_API_KEY: Optional[str] = None
    BRIEF_TIMEZONE: str = "Australia/Melbourne"

    # Social/discussion highlights. Each source self-gates: Reddit/Bluesky need
    # creds (below); the news source needs only a feeds file (no creds). The
    # backfill runs when ≥1 source is available AND DEEPSEEK_API_KEY is set; with
    # no source available the panel stays dark.
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "wc2026-social/0.1"
    BLUESKY_IDENTIFIER: Optional[str] = None
    BLUESKY_APP_PASSWORD: Optional[str] = None
    # News source: path to a JSON file of RSS/Atom feeds ({"feeds": [{name, url}]}).
    # Defaults to the bundled app/social/news_feeds.json; override to point at a
    # file mounted on the VM so feeds can change without a rebuild. The news source
    # is available whenever the file has ≥1 valid feed (no credentials needed).
    SOCIAL_NEWS_FEEDS_FILE: Optional[str] = None
    # X (Twitter) candidates are collected out-of-band by a local browser script
    # (X's API is paid) and dropped onto the VM as a JSON file; the collector reads
    # it here and folds them into curation. None → no X candidates. Stale files
    # (older than SOCIAL_X_MAX_AGE_HOURS) are ignored so a dead nightly job can't
    # keep resurfacing old posts.
    SOCIAL_X_CANDIDATES_FILE: Optional[str] = None
    SOCIAL_X_MAX_AGE_HOURS: int = 36
    SOCIAL_HIGHLIGHTS_MAX: int = 3        # curated highlights stored per fixture
    SOCIAL_LOOKBACK_HOURS: int = 48       # only consider posts newer than this
    SOCIAL_LOOKAHEAD_HOURS: int = 48      # only fixtures kicking off within this window
    SOCIAL_MAX_FIXTURES_PER_RUN: int = 12  # hard cap on per-run DeepSeek fan-out
    SOCIAL_CANDIDATE_CAP: int = 30        # pre-trim cap handed to the LLM

    # Live poller: how often to hit ?live=all while a match is in its window,
    # how long to sleep when no match is live, and the post-kickoff window
    # during which a fixture is considered possibly-in-play.
    LIVE_POLL_SECONDS: int = 120
    IDLE_SLEEP_SECONDS: int = 300
    LIVE_WINDOW_HOURS: int = 3

    # App logging: persist INFO+ events to app_logs and prune rows older than
    # LOG_RETENTION_DAYS. LOG_DB_ENABLED=False keeps stdout-only (tests/local).
    LOG_RETENTION_DAYS: int = 14
    LOG_DB_ENABLED: bool = True

    # LangSmith tracing (optional). Off unless TRACING is true AND a key is set,
    # so CI/local stay untraced by default. LANGSMITH_ENV is a trace tag only.
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "worldcup-2026"
    LANGSMITH_ENV: str = "dev"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"


settings = Settings()
