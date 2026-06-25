"""Social discussion collection: free-source adapters (Reddit, Bluesky) that
fetch fan discussion about upcoming matches, plus shared candidate plumbing.

No LLM here — curation/safety lives in app.social.select. Everything is gated on
credentials: a source with no creds reports `available() is False` and is skipped."""
from app.social.base import (
    Candidate,
    SocialSource,
    build_query,
    dedupe,
    is_http_url,
    pretrim,
)

__all__ = [
    "Candidate",
    "SocialSource",
    "build_query",
    "dedupe",
    "is_http_url",
    "pretrim",
]
