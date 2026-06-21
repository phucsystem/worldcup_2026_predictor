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
