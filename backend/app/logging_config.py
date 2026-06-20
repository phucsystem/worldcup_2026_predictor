"""Centralized, non-blocking application logging.

One `configure_logging()` wires every process to log to stdout AND to the
`app_logs` table without ever blocking or crashing the caller. Invariants
(see the logging plan's `plan.md`):

  - **Non-blocking**: app loggers only enqueue (a `QueueHandler`); all I/O runs
    on a background `QueueListener` thread.
  - **Never crashes**: the DB handler swallows its own errors to stderr.
  - **No feedback loop**: `sqlalchemy`/`psycopg` logs are quieted and excluded
    from the DB handler, so persisting a row can never emit a logged row.
  - **No lost records**: short-lived processes flush on exit (`atexit`, plus an
    explicit `stop_logging()` in CLI `finally` blocks).
  - **INFO floor for persistence**: the DB handler is INFO-level; DEBUG records
    reach stdout only.
"""
from __future__ import annotations

import atexit
import logging
import logging.handlers
import queue
import sys
import threading
from datetime import datetime, timezone

BATCH_SIZE = 50
FLUSH_INTERVAL_SECONDS = 2.0

# Loggers whose own output must never be persisted: the DB write path runs
# through these, so persisting their records would feed the handler and recurse.
_EXCLUDED_PREFIXES = ("sqlalchemy", "psycopg", "aiosqlite")

# LogRecord attributes (set via `logger.x(..., extra={...})`) copied into
# context["extra"]. `run_id` is promoted to its own column, so it's excluded here.
_EXTRA_WHITELIST = ("node", "attempt", "fixture_id", "brief_date")

# Stateless formatter, used only for rendering exception tracebacks off-thread.
_FORMATTER = logging.Formatter()

_configured = False
_listener: logging.handlers.QueueListener | None = None
_db_handler: "DBLogHandler | None" = None


class _RawQueueHandler(logging.handlers.QueueHandler):
    """QueueHandler that enqueues the record untouched.

    The default `prepare()` formats the message and *clears* `exc_info`, which
    would strip tracebacks before the DB handler (running on the listener thread)
    can capture them. We use an in-process queue, so passing the raw record is
    safe and lets each downstream handler format independently."""

    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        return record


class _DBExclusionFilter(logging.Filter):
    """Drop records that must not be persisted (recursion guard)."""

    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name
        return not any(name == p or name.startswith(p + ".") for p in _EXCLUDED_PREFIXES)


class DBLogHandler(logging.Handler):
    """Buffers `LogRecord`s and flushes them to `app_logs` in batches on a
    background thread. Owns its own session factory — never touches request
    sessions. Every failure is swallowed to stderr; nothing propagates to
    callers. Runs at INFO level so DEBUG is never persisted."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self._buffer: list[dict] = []
        self._lock = threading.Lock()
        self._session_factory = None
        self._stop = threading.Event()
        self._flusher = threading.Thread(
            target=self._flush_loop, name="db-log-flusher", daemon=True
        )
        self._flusher.start()

    def _record_to_row(self, record: logging.LogRecord) -> dict:
        context: dict = {}
        if record.exc_info:
            context["traceback"] = _FORMATTER.formatException(record.exc_info)
        if record.stack_info:
            context["stack"] = record.stack_info
        extra = {k: getattr(record, k) for k in _EXTRA_WHITELIST if hasattr(record, k)}
        if extra:
            context["extra"] = extra
        return {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc),
            "level": record.levelname,
            "source": record.name,
            "message": record.getMessage(),
            "context": context or None,
            "run_id": getattr(record, "run_id", None),
        }

    def emit(self, record: logging.LogRecord) -> None:
        try:
            row = self._record_to_row(record)
            with self._lock:
                self._buffer.append(row)
                full = len(self._buffer) >= BATCH_SIZE
            if full:
                self._flush()
        except Exception:
            self.handleError(record)

    def _flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            rows, self._buffer = self._buffer, []
        try:
            from app.data.repository import insert_log_rows, make_session_factory

            if self._session_factory is None:
                self._session_factory = make_session_factory()
            with self._session_factory() as session:
                insert_log_rows(session, rows)
        except Exception as exc:  # never raise into the app; drop the batch
            print(
                f"[DBLogHandler] dropped {len(rows)} log rows: {exc}",
                file=sys.stderr,
            )

    def _flush_loop(self) -> None:
        while not self._stop.wait(FLUSH_INTERVAL_SECONDS):
            self._flush()

    def close(self) -> None:
        self._stop.set()
        self._flusher.join(timeout=5.0)
        self._flush()
        super().close()

    def handleError(self, record: logging.LogRecord) -> None:
        try:
            print(
                f"[DBLogHandler] error handling a log record from {record.name}",
                file=sys.stderr,
            )
        except Exception:
            pass


def configure_logging(*, db: bool | None = None) -> None:
    """Idempotently configure process logging. Safe to call from any entrypoint
    (and more than once, e.g. uvicorn reload)."""
    global _configured, _listener, _db_handler
    if _configured:
        return

    from app.config import settings

    db_enabled = settings.LOG_DB_ENABLED if db is None else db

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))

    handlers: list[logging.Handler] = [console]
    if db_enabled:
        _db_handler = DBLogHandler()
        _db_handler.addFilter(_DBExclusionFilter())
        handlers.append(_db_handler)

    log_queue: queue.Queue = queue.Queue(-1)
    _listener = logging.handlers.QueueListener(
        log_queue, *handlers, respect_handler_level=True
    )
    _listener.start()

    root = logging.getLogger()
    # Drop any prior basicConfig handlers so records aren't double-emitted.
    for h in root.handlers[:]:
        root.removeHandler(h)
    # Root floor is INFO for clean default output. A logger explicitly set to
    # DEBUG (e.g. `getLogger("app.x").setLevel(DEBUG)`) still routes to stdout
    # (console floor=DEBUG) but never to the DB (handler floor=INFO) — that is
    # the "DEBUG to stdout only" guarantee, without flooding prod stdout.
    root.setLevel(logging.INFO)
    root.addHandler(_RawQueueHandler(log_queue))

    # Quiet chatty libraries: keeps stdout readable and, combined with the DB
    # exclusion filter, prevents a write-triggered log from feeding the handler.
    for noisy in ("sqlalchemy", "sqlalchemy.engine", "httpx", "httpcore",
                  "urllib3", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    atexit.register(stop_logging)
    _configured = True


def start_logging() -> None:
    """Explicit start (configure already starts the listener)."""
    if not _configured:
        configure_logging()


def stop_logging() -> None:
    """Stop the listener and flush buffered records. Idempotent — safe to call
    from a CLI `finally` and again via `atexit`."""
    global _listener, _db_handler
    listener, _listener = _listener, None
    if listener is not None:
        listener.stop()  # drains the queue, then the loop exits
    handler, _db_handler = _db_handler, None
    if handler is not None:
        handler.close()  # final flush of any partial batch
