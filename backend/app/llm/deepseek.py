from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI


_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_DEEPSEEK_MODEL = "deepseek-chat"

# Cost per 1M tokens (USD) — deepseek-chat pricing
_COST_PER_M_INPUT = 0.27
_COST_PER_M_OUTPUT = 1.10


def make_client() -> "ChatOpenAI":
    """Lazy factory — never called at import time; safe in CI without a key."""
    from langchain_openai import ChatOpenAI

    from app.config import settings

    return ChatOpenAI(
        base_url=_DEEPSEEK_BASE_URL,
        model=_DEEPSEEK_MODEL,
        api_key=settings.DEEPSEEK_API_KEY or "no-key",
        temperature=0.7,
    )


def make_structured_client(schema: Type[Any]) -> "ChatOpenAI":
    """Structured output bound to `schema`.

    include_raw=True so invoke() returns {"raw": AIMessage, "parsed": schema, ...};
    the raw message carries usage_metadata for token/cost logging.
    """
    return make_client().with_structured_output(schema, method="json_mode", include_raw=True)


def usage_from_raw(raw: Any) -> tuple[int, int]:
    """Extract (input_tokens, output_tokens) from a raw AIMessage; 0s if absent."""
    meta = getattr(raw, "usage_metadata", None) or {}
    return int(meta.get("input_tokens", 0) or 0), int(meta.get("output_tokens", 0) or 0)


def estimate_cost(tokens_in: int, tokens_out: int) -> float:
    return (tokens_in / 1_000_000) * _COST_PER_M_INPUT + (
        tokens_out / 1_000_000
    ) * _COST_PER_M_OUTPUT
