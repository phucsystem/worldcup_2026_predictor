"""Feedback API validation (pure) + repository helpers (in-memory SQLite)."""
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.feedback import FeedbackIn, StatusIn
from app.data import repository as repo


# ---------------------------------------------------------------------------
# Pydantic validation (pure)
# ---------------------------------------------------------------------------

class TestFeedbackIn:
    def test_strips_message(self):
        assert FeedbackIn(message="  hello  ").message == "hello"

    def test_blank_message_rejected(self):
        with pytest.raises(ValueError):
            FeedbackIn(message="   ")

    def test_topic_whitelist_passes_known(self):
        assert FeedbackIn(message="x", topic="bug").topic == "bug"

    def test_topic_unknown_coerced_to_other(self):
        assert FeedbackIn(message="x", topic="spam").topic == "other"

    def test_topic_none_stays_none(self):
        assert FeedbackIn(message="x").topic is None

    def test_overlong_message_rejected(self):
        with pytest.raises(ValueError):
            FeedbackIn(message="a" * 2001)


class TestStatusIn:
    @pytest.mark.parametrize("s", ["new", "done", "wont"])
    def test_valid(self, s):
        assert StatusIn(status=s).status == s

    def test_invalid_rejected(self):
        with pytest.raises(ValueError):
            StatusIn(status="archived")


# ---------------------------------------------------------------------------
# Repository helpers (in-memory SQLite)
# ---------------------------------------------------------------------------

@pytest.fixture
def session():
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    repo.feedback_table.create(bind=engine)
    factory = sessionmaker(bind=engine)
    s = factory()
    try:
        yield s
    finally:
        s.close()


class TestFeedbackRepo:
    def test_insert_then_list(self, session):
        fid = repo.insert_feedback(session, message="great", topic="feature", page="/")
        rows = repo.list_feedback(session)
        assert len(rows) == 1
        assert rows[0].id == fid
        assert rows[0].status == "new"
        assert rows[0].topic == "feature"
        assert rows[0].page == "/"
        assert rows[0].resolved_at is None

    def test_list_newest_first(self, session):
        repo.insert_feedback(session, message="first")
        second = repo.insert_feedback(session, message="second")
        rows = repo.list_feedback(session)
        assert rows[0].id == second

    def test_status_filter(self, session):
        a = repo.insert_feedback(session, message="a")
        repo.insert_feedback(session, message="b")
        repo.set_feedback_status(session, a, "done")
        assert len(repo.list_feedback(session, status="done")) == 1
        assert len(repo.list_feedback(session, status="new")) == 1

    def test_set_status_stamps_resolved_at(self, session):
        fid = repo.insert_feedback(session, message="x")
        repo.set_feedback_status(session, fid, "done")
        row = repo.list_feedback(session)[0]
        assert row.status == "done"
        assert row.resolved_at is not None

    def test_reopen_clears_resolved_at(self, session):
        fid = repo.insert_feedback(session, message="x")
        repo.set_feedback_status(session, fid, "wont")
        repo.set_feedback_status(session, fid, "new")
        row = repo.list_feedback(session)[0]
        assert row.status == "new"
        assert row.resolved_at is None

    def test_set_status_missing_id_returns_false(self, session):
        assert repo.set_feedback_status(session, 9999, "done") is False

    def test_set_status_invalid_raises(self, session):
        fid = repo.insert_feedback(session, message="x")
        with pytest.raises(ValueError):
            repo.set_feedback_status(session, fid, "archived")
