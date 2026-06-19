from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://wc:wc@localhost:5432/worldcup"
    API_FOOTBALL_KEY: Optional[str] = None
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"
    DEEPSEEK_API_KEY: Optional[str] = None
    BRIEF_TIMEZONE: str = "Australia/Melbourne"


settings = Settings()
