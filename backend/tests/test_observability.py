"""Tests for the env-gated LangSmith tracing bootstrap.

Covers the four contracts that keep CI/local untraced and crash-free:
off-by-default, on-when-configured, idempotent, and never-raises.
"""
import app.observability as obs
from app.config import settings

_LS_VARS = ("LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT", "LANGSMITH_ENDPOINT")


def _reset(monkeypatch):
    """Fresh bootstrap state: clear the idempotency latch and any LANGSMITH_* env."""
    monkeypatch.setattr(obs, "_configured", False)
    for var in _LS_VARS:
        monkeypatch.delenv(var, raising=False)


def test_disabled_when_flag_off(monkeypatch):
    _reset(monkeypatch)
    monkeypatch.setattr(settings, "LANGSMITH_TRACING", False)
    monkeypatch.setattr(settings, "LANGSMITH_API_KEY", "sk-fake")

    assert obs.configure_tracing() is False
    import os
    assert os.environ.get("LANGSMITH_TRACING") != "true"


def test_disabled_when_key_missing(monkeypatch):
    _reset(monkeypatch)
    monkeypatch.setattr(settings, "LANGSMITH_TRACING", True)
    monkeypatch.setattr(settings, "LANGSMITH_API_KEY", None)

    assert obs.configure_tracing() is False
    import os
    assert os.environ.get("LANGSMITH_TRACING") != "true"


def test_enabled_exports_env(monkeypatch):
    _reset(monkeypatch)
    monkeypatch.setattr(settings, "LANGSMITH_TRACING", True)
    monkeypatch.setattr(settings, "LANGSMITH_API_KEY", "sk-fake")
    monkeypatch.setattr(settings, "LANGSMITH_PROJECT", "test-proj")
    monkeypatch.setattr(settings, "LANGSMITH_ENDPOINT", "https://example.test")

    assert obs.configure_tracing() is True
    import os
    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "sk-fake"
    assert os.environ["LANGSMITH_PROJECT"] == "test-proj"
    assert os.environ["LANGSMITH_ENDPOINT"] == "https://example.test"


def test_idempotent_second_call_is_noop(monkeypatch):
    _reset(monkeypatch)
    monkeypatch.setattr(settings, "LANGSMITH_TRACING", True)
    monkeypatch.setattr(settings, "LANGSMITH_API_KEY", "sk-fake")

    assert obs.configure_tracing() is True
    # Flip settings off; latched state means the second call must not re-evaluate.
    monkeypatch.setattr(settings, "LANGSMITH_TRACING", False)
    assert obs.configure_tracing() is True


def test_never_raises_on_internal_error(monkeypatch):
    _reset(monkeypatch)

    class _Boom:
        def __getattr__(self, name):
            raise RuntimeError("settings exploded")

    monkeypatch.setattr("app.config.settings", _Boom())

    # Must swallow the error and report disabled, not propagate.
    assert obs.configure_tracing() is False
