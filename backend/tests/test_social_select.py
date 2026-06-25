"""Unit tests for social highlight curation.

The structured DeepSeek client is mocked at the make_structured_client boundary,
so no network/LLM is hit. Asserts index-resolution (no fabrication), clamping,
url-drop, keep-last-good, and credential gating.
"""
import app.llm.deepseek as deepseek
from app.config import settings
from app.social.base import Candidate
from app.social.select import HighlightSelection, SelectedHighlight, generate_social_highlights


def _cands(n=4):
    return [
        Candidate(source="reddit", url=f"https://r.com/{i}", author=f"u/{i}",
                  text=f"insight number {i}", engagement=i)
        for i in range(n)
    ]


class _FakeClient:
    def __init__(self, selection):
        self._selection = selection
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return {"parsed": self._selection}


def _patch(monkeypatch, selection, *, key="test-key"):
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", key)
    client = _FakeClient(selection) if selection is not None else None
    if client is not None:
        monkeypatch.setattr(deepseek, "make_structured_client", lambda schema: client)
    return client


def test_valid_selection_resolves_real_fields(monkeypatch):
    sel = HighlightSelection(selected=[
        SelectedHighlight(index=2, why="sharp take"),
        SelectedHighlight(index=0, why="good context"),
    ])
    _patch(monkeypatch, sel)
    result = generate_social_highlights("Brazil", "Serbia", _cands())
    assert result is not None
    blob, model = result
    assert model == "deepseek-chat"
    hs = blob["highlights"]
    assert [h["url"] for h in hs] == ["https://r.com/2", "https://r.com/0"]
    assert hs[0]["why"] == "sharp take"
    assert hs[0]["author"] == "u/2"  # resolved from candidate, not the model


def test_out_of_range_and_duplicate_indices_dropped(monkeypatch):
    sel = HighlightSelection(selected=[
        SelectedHighlight(index=99, why="x"),   # out of range
        SelectedHighlight(index=1, why="ok"),
        SelectedHighlight(index=1, why="dup"),  # duplicate
    ])
    _patch(monkeypatch, sel)
    blob, _ = generate_social_highlights("A", "B", _cands())
    assert [h["url"] for h in blob["highlights"]] == ["https://r.com/1"]


def test_clamped_to_max(monkeypatch):
    monkeypatch.setattr(settings, "SOCIAL_HIGHLIGHTS_MAX", 2)
    sel = HighlightSelection(selected=[SelectedHighlight(index=i, why=f"w{i}") for i in range(4)])
    _patch(monkeypatch, sel)
    blob, _ = generate_social_highlights("A", "B", _cands())
    assert len(blob["highlights"]) == 2


def test_nonhttp_url_candidate_dropped(monkeypatch):
    cands = [Candidate(source="reddit", url="javascript:alert(1)", author="u/x", text="evil", engagement=5)]
    sel = HighlightSelection(selected=[SelectedHighlight(index=0, why="x")])
    _patch(monkeypatch, sel)
    # A Candidate with a bad url should never have been built by Phase 2, but if it
    # reaches here the resolver drops it → nothing selected → keep-last-good None.
    assert generate_social_highlights("A", "B", cands) is None


def test_empty_candidates_returns_none(monkeypatch):
    _patch(monkeypatch, HighlightSelection(selected=[]))
    assert generate_social_highlights("A", "B", []) is None


def test_no_api_key_returns_none_without_call(monkeypatch):
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", None)
    # make_structured_client must never be called.
    monkeypatch.setattr(deepseek, "make_structured_client",
                        lambda schema: (_ for _ in ()).throw(AssertionError("called")))
    assert generate_social_highlights("A", "B", _cands()) is None


def test_model_failure_twice_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "test-key")

    class _Boom:
        def invoke(self, messages):
            raise RuntimeError("LLM down")

    monkeypatch.setattr(deepseek, "make_structured_client", lambda schema: _Boom())
    assert generate_social_highlights("A", "B", _cands()) is None


def test_long_text_is_truncated(monkeypatch):
    long = "word " * 200
    cands = [Candidate(source="reddit", url="https://r.com/x", author="u/x", text=long, engagement=1)]
    sel = HighlightSelection(selected=[SelectedHighlight(index=0, why="long")])
    _patch(monkeypatch, sel)
    blob, _ = generate_social_highlights("A", "B", cands)
    assert len(blob["highlights"][0]["text"]) <= 280
